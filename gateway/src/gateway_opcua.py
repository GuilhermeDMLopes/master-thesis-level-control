from __future__ import annotations

import asyncio
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from asyncua import Server, ua

from gateway_config import (
    BR_APPLIED_DAC_NODE_ID,
    BR_APPLIED_ENABLE_NODE_ID,
    BR_DAC_NODE_ID,
    BR_ENABLE_NODE_ID,
    BR_ENDPOINT,
    BR_HEARTBEAT_NODE_ID,
    BR_LEVEL_NODE_ID,
    BR_RECONNECT_INTERVAL_S,
    BR_SAFETY_RESET_NODE_ID,
    BR_WATCHDOG_HEALTHY_NODE_ID,
    BR_WATCHDOG_TRIPPED_NODE_ID,
    CSV_PATH,
    DAC_BOUNDARY_MAX,
    DAC_BOUNDARY_MAX_DELTA,
    DAC_BOUNDARY_MIN,
    DAC_LIMITER_MAX,
    DAC_LIMITER_MAX_DELTA,
    DAC_LIMITER_MIN,
    DAC_LIMITER_RESET,
    GATEWAY_APPLIED_DAC_NODE_ID,
    GATEWAY_APPLIED_ENABLE_NODE_ID,
    GATEWAY_CYCLE_TIME_S,
    GATEWAY_DAC_FEEDBACK_NODE_ID,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
    GATEWAY_ENDPOINT,
    GATEWAY_NAMESPACE_URI,
    GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
    GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
    LEVEL_SCALE,
    LOG_PERIOD_S,
    PI_KD,
    PI_KI,
    PI_KP,
    PI_MANUAL_MODE,
    PI_MANUAL_OUTPUT,
    PI_RESET,
    PI_SAMPLING_TIME_S,
    PI_SETPOINT_CM,
    PI_SETPOINT_RAW_EQUIVALENT,
    PV_FILTER_ALPHA,
    PV_FILTER_RESET,
    WATCHDOG_HEARTBEAT_PERIOD_S,
    WATCHDOG_RESET_PULSE_S,
    WATCHDOG_STARTUP_POLL_PERIOD_S,
    WATCHDOG_STARTUP_TIMEOUT_S,
)

from gateway_connection import (
    BrConnection,
    BrRuntimeState,
    close_br_connection,
    open_br_connection,
    read_br_runtime_state,
)

from gateway_interface import (
    GatewayVariables,
    create_gateway_variables,
    publish_disconnected_safe_state,
    publish_plc_feedback_values,
)

from gateway_processing import (
    dac_to_percent,
    limit_dac_boundary_step,
    raw_level_to_cm,
    update_filtered_value,
)

from gateway_watchdog import (
    WatchdogStartupResult,
    initialize_plc_watchdog,
    watchdog_permits_commands,
    write_next_heartbeat,
    write_safe_plc_commands,
    write_value_only,
)


# ============================================================
# CSV CONFIGURATION
# ============================================================

COMMUNICATION_STATE_CONNECTED = "CONNECTED"
COMMUNICATION_STATE_RECONNECTED = "RECONNECTED"

CSV_HEADER = (
    "timestamp",
    "elapsed_time_s",
    "level_raw",
    "level_cm",
    "level_filtered_gateway_cm",
    "setpoint_raw_equivalent",
    "setpoint_cm",
    "error_cm",
    "filtered_error_gateway_cm",
    "dac_gateway_command",
    "dac_br_feedback",
    "mv_gateway_percent",
    "mv_br_percent",
    "enable_gateway_command",
    "enable_br_feedback",
    "kp",
    "ki",
    "kd",
    "sampling_time_s",
    "manual_mode",
    "manual_output",
    "reset",
    "pv_filter_alpha",
    "pv_filter_reset",
    "dac_limiter_max_delta",
    "dac_limiter_min",
    "dac_limiter_max",
    "dac_limiter_reset",
    "level_scale",
    "notes",
    "communication_state",
    "reconnection_count",
    "dac_gateway_applied",
    "mv_gateway_applied_percent",
    "dac_boundary_limited",
    "dac_boundary_max_delta",
    "heartbeat_gateway_value",
    "safety_reset_br_feedback",
    "watchdog_healthy",
    "watchdog_tripped",
    "applied_enable",
    "applied_dac",
    "watchdog_commands_permitted",
)


# ============================================================
# AUXILIARY FUNCTIONS
# ============================================================

def open_csv_logger(file_path: Path) -> tuple[Any, csv.writer]:
    """Create the experiment CSV file and write its header."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    csv_file = file_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    )
    writer = csv.writer(
        csv_file,
        delimiter=";",
    )

    writer.writerow(CSV_HEADER)

    csv_file.flush()
    return csv_file, writer


async def set_gateway_command_variables_safe(
    gateway_variables: GatewayVariables,
) -> None:
    """Discard pending client commands in the gateway address space."""
    await gateway_variables.enable_command.write_value(
        ua.Variant(
            False,
            ua.VariantType.Boolean,
        )
    )
    await gateway_variables.dac_command.write_value(
        ua.Variant(
            0,
            ua.VariantType.Int16,
        )
    )


async def publish_runtime_state(
    *,
    gateway_variables: GatewayVariables,
    state: BrRuntimeState,
) -> None:
    """Publish one PLC runtime state to the gateway server."""
    await gateway_variables.level.write_value(
        ua.Variant(
            float(state.raw_level),
            ua.VariantType.Double,
        )
    )

    await publish_plc_feedback_values(
        enable_feedback_variable=(
            gateway_variables.enable_feedback
        ),
        dac_feedback_variable=gateway_variables.dac_feedback,
        watchdog_healthy_variable=(
            gateway_variables.watchdog_healthy
        ),
        watchdog_tripped_variable=(
            gateway_variables.watchdog_tripped
        ),
        applied_enable_variable=(
            gateway_variables.applied_enable
        ),
        applied_dac_variable=gateway_variables.applied_dac,
        confirmed_enable=state.enable,
        confirmed_dac=state.dac,
        watchdog_healthy=state.watchdog_healthy,
        watchdog_tripped=state.watchdog_tripped,
        applied_enable=state.applied_enable,
        applied_dac=state.applied_dac,
    )


async def publish_gateway_disconnected_state(
    gateway_variables: GatewayVariables,
) -> None:
    """Discard commands and expose a fail-closed disconnected state."""
    await set_gateway_command_variables_safe(
        gateway_variables
    )

    await publish_disconnected_safe_state(
        enable_feedback_variable=(
            gateway_variables.enable_feedback
        ),
        dac_feedback_variable=gateway_variables.dac_feedback,
        watchdog_healthy_variable=(
            gateway_variables.watchdog_healthy
        ),
        watchdog_tripped_variable=(
            gateway_variables.watchdog_tripped
        ),
        applied_enable_variable=(
            gateway_variables.applied_enable
        ),
        applied_dac_variable=gateway_variables.applied_dac,
    )


# ============================================================
# GATEWAY SYNCHRONIZATION
# ============================================================

async def synchronize_after_reconnection(
    *,
    connection: BrConnection,
    gateway_variables: GatewayVariables,
) -> BrRuntimeState:
    """
    Publish confirmed PLC state and discard commands queued offline.

    The PLC watchdog handshake has already forced Enable=False and DAC=0.
    The writable gateway command nodes are explicitly reset to those safe
    values before any FORTE command can be processed.
    """
    state = await read_br_runtime_state(connection)

    if (
        state.enable
        or state.dac != 0
        or state.applied_enable
        or state.applied_dac != 0
    ):
        raise RuntimeError(
            "PLC state was not safe after watchdog initialization"
        )

    await set_gateway_command_variables_safe(
        gateway_variables
    )
    await publish_runtime_state(
        gateway_variables=gateway_variables,
        state=state,
    )

    return state


def connection_error_text(error: BaseException) -> str:
    """Return a concise connection error description for gateway logs."""
    detail = str(error).strip()

    if detail:
        return f"{error.__class__.__name__}: {detail}"

    return error.__class__.__name__


async def open_watchdog_protected_connection() -> tuple[
    BrConnection,
    WatchdogStartupResult,
]:
    """Open the PLC connection and complete the fail-closed handshake."""
    connection = await open_br_connection(
        endpoint=BR_ENDPOINT,
        level_node_id=BR_LEVEL_NODE_ID,
        enable_node_id=BR_ENABLE_NODE_ID,
        dac_node_id=BR_DAC_NODE_ID,
        heartbeat_node_id=BR_HEARTBEAT_NODE_ID,
        safety_reset_node_id=BR_SAFETY_RESET_NODE_ID,
        watchdog_healthy_node_id=BR_WATCHDOG_HEALTHY_NODE_ID,
        watchdog_tripped_node_id=BR_WATCHDOG_TRIPPED_NODE_ID,
        applied_enable_node_id=BR_APPLIED_ENABLE_NODE_ID,
        applied_dac_node_id=BR_APPLIED_DAC_NODE_ID,
    )

    try:
        startup_result = await initialize_plc_watchdog(
            connection=connection,
            heartbeat_period_s=(
                WATCHDOG_HEARTBEAT_PERIOD_S
            ),
            reset_pulse_s=WATCHDOG_RESET_PULSE_S,
            startup_timeout_s=(
                WATCHDOG_STARTUP_TIMEOUT_S
            ),
            poll_period_s=(
                WATCHDOG_STARTUP_POLL_PERIOD_S
            ),
        )
    except Exception:
        await close_br_connection(connection)
        raise

    return connection, startup_result


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    br_connection: BrConnection | None = None
    gateway_variables: GatewayVariables | None = None
    csv_file = None
    filtered_level_gateway_cm: float | None = None

    try:
        logging.info(
            "Connecting to the B&R OPC UA server: %s",
            BR_ENDPOINT,
        )

        (
            br_connection,
            startup_result,
        ) = await open_watchdog_protected_connection()

        initial_state = startup_result.state
        heartbeat_value = startup_result.heartbeat_value
        last_heartbeat_write_time = time.monotonic()

        logging.info(
            "Connected to the B&R OPC UA server with a healthy watchdog."
        )
        logging.info("Initial safe values read from the B&R PLC:")
        logging.info(
            "  Raw level       = %s",
            initial_state.raw_level,
        )
        logging.info(
            "  Provisional cm  = %.3f",
            raw_level_to_cm(initial_state.raw_level),
        )
        logging.info(
            "  Enable command  = %s",
            initial_state.enable,
        )
        logging.info(
            "  DAC command     = %s",
            initial_state.dac,
        )
        logging.info(
            "  WatchdogHealthy = %s",
            initial_state.watchdog_healthy,
        )
        logging.info(
            "  WatchdogTripped = %s",
            initial_state.watchdog_tripped,
        )
        logging.info(
            "  AppliedEnable   = %s",
            initial_state.applied_enable,
        )
        logging.info(
            "  AppliedDAC      = %s",
            initial_state.applied_dac,
        )

        filtered_level_gateway_cm = raw_level_to_cm(
            initial_state.raw_level
        )

        server = Server()
        await server.init()
        server.set_endpoint(GATEWAY_ENDPOINT)
        server.set_server_name(
            "B&R to 4diac OPC UA Gateway"
        )

        namespace_index = await server.register_namespace(
            GATEWAY_NAMESPACE_URI
        )

        gateway_object = await server.nodes.objects.add_object(
            namespace_index,
            "BR_Gateway",
        )

        gateway_variables = await create_gateway_variables(
            gateway_object=gateway_object,
            namespace_index=namespace_index,
            initial_raw_level=initial_state.raw_level,
            initial_enable=False,
            initial_dac=0,
            initial_watchdog_healthy=(
                initial_state.watchdog_healthy
            ),
            initial_watchdog_tripped=(
                initial_state.watchdog_tripped
            ),
            initial_applied_enable=(
                initial_state.applied_enable
            ),
            initial_applied_dac=initial_state.applied_dac,
        )

        last_enable_command = False
        boundary_reference_dac = 0
        last_gateway_applied_dac = 0
        dac_boundary_limited = False

        # Validate the final write-boundary limiter before accepting commands.
        limit_dac_boundary_step(
            requested_dac=0,
            reference_dac=0,
            maximum_delta=DAC_BOUNDARY_MAX_DELTA,
            dac_min=DAC_BOUNDARY_MIN,
            dac_max=DAC_BOUNDARY_MAX,
        )

        csv_file, csv_writer = open_csv_logger(CSV_PATH)
        logging.info(
            "Experiment CSV created at: %s",
            CSV_PATH,
        )

        start_time = time.monotonic()
        last_log_time = 0.0
        next_reconnect_time = 0.0
        reconnection_count = 0
        communication_state = COMMUNICATION_STATE_CONNECTED
        watchdog_fault_reported = False

        async with server:
            logging.info(
                "Gateway OPC UA server running at: %s",
                GATEWAY_ENDPOINT,
            )
            logging.info(
                "Gateway namespace registered as ns=%s",
                namespace_index,
            )
            logging.info(
                (
                    "PLC watchdog: heartbeat period=%.3fs, "
                    "startup timeout=%.3fs"
                ),
                WATCHDOG_HEARTBEAT_PERIOD_S,
                WATCHDOG_STARTUP_TIMEOUT_S,
            )
            logging.info(
                (
                    "Final DAC boundary limiter: maximum delta=%s, "
                    "minimum=%s, maximum=%s"
                ),
                DAC_BOUNDARY_MAX_DELTA,
                DAC_BOUNDARY_MIN,
                DAC_BOUNDARY_MAX,
            )
            logging.info("NodeIds expected by 4diac FORTE:")
            logging.info(
                "  ns=%s;s=Nivel [Double/LREAL, raw level]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=Enable [Boolean, command]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=DAC [Int16, command]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=%s [Boolean, PLC command feedback]",
                namespace_index,
                GATEWAY_ENABLE_FEEDBACK_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Int16, PLC command feedback]",
                namespace_index,
                GATEWAY_DAC_FEEDBACK_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Boolean, read only]",
                namespace_index,
                GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Boolean, read only]",
                namespace_index,
                GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Boolean, read only]",
                namespace_index,
                GATEWAY_APPLIED_ENABLE_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Int16, read only]",
                namespace_index,
                GATEWAY_APPLIED_DAC_NODE_ID,
            )

            while True:
                elapsed_time_s = (
                    time.monotonic() - start_time
                )

                if br_connection is None:
                    current_time = time.monotonic()

                    if current_time >= next_reconnect_time:
                        logging.info(
                            (
                                "Attempting watchdog-protected "
                                "reconnection to: %s"
                            ),
                            BR_ENDPOINT,
                        )

                        try:
                            (
                                candidate_connection,
                                candidate_startup,
                            ) = (
                                await open_watchdog_protected_connection()
                            )

                            synchronized_state = (
                                await synchronize_after_reconnection(
                                    connection=candidate_connection,
                                    gateway_variables=gateway_variables,
                                )
                            )

                        except Exception as error:
                            next_reconnect_time = (
                                time.monotonic()
                                + BR_RECONNECT_INTERVAL_S
                            )

                            logging.warning(
                                (
                                    "Reconnection or watchdog handshake "
                                    "failed (%s). Next attempt in %.1f s."
                                ),
                                connection_error_text(error),
                                BR_RECONNECT_INTERVAL_S,
                            )

                        else:
                            br_connection = candidate_connection
                            heartbeat_value = (
                                candidate_startup.heartbeat_value
                            )
                            last_heartbeat_write_time = (
                                time.monotonic()
                            )

                            filtered_level_gateway_cm = (
                                raw_level_to_cm(
                                    synchronized_state.raw_level
                                )
                            )
                            last_enable_command = False
                            boundary_reference_dac = 0
                            last_gateway_applied_dac = 0
                            dac_boundary_limited = False
                            last_log_time = elapsed_time_s
                            reconnection_count += 1
                            communication_state = (
                                COMMUNICATION_STATE_RECONNECTED
                            )
                            watchdog_fault_reported = False

                            logging.info(
                                (
                                    "PLC communication and watchdog "
                                    "restored. Offline commands were "
                                    "discarded."
                                )
                            )

                    await asyncio.sleep(
                        GATEWAY_CYCLE_TIME_S
                    )
                    continue

                try:
                    current_time = time.monotonic()

                    if (
                        current_time
                        - last_heartbeat_write_time
                        >= WATCHDOG_HEARTBEAT_PERIOD_S
                    ):
                        heartbeat_value = (
                            await write_next_heartbeat(
                                br_connection,
                                heartbeat_value,
                            )
                        )
                        last_heartbeat_write_time = (
                            current_time
                        )

                    state = await read_br_runtime_state(
                        br_connection
                    )

                    await publish_runtime_state(
                        gateway_variables=gateway_variables,
                        state=state,
                    )

                    commands_permitted = (
                        watchdog_permits_commands(
                            healthy=state.watchdog_healthy,
                            tripped=state.watchdog_tripped,
                        )
                    )

                    if not commands_permitted:
                        if not watchdog_fault_reported:
                            logging.warning(
                                (
                                    "PLC watchdog is not healthy. "
                                    "Gateway commands are blocked and "
                                    "a safe re-arm will be attempted."
                                )
                            )
                            watchdog_fault_reported = True

                        await set_gateway_command_variables_safe(
                            gateway_variables
                        )

                        rearm_result = (
                            await initialize_plc_watchdog(
                                connection=br_connection,
                                heartbeat_period_s=(
                                    WATCHDOG_HEARTBEAT_PERIOD_S
                                ),
                                reset_pulse_s=(
                                    WATCHDOG_RESET_PULSE_S
                                ),
                                startup_timeout_s=(
                                    WATCHDOG_STARTUP_TIMEOUT_S
                                ),
                                poll_period_s=(
                                    WATCHDOG_STARTUP_POLL_PERIOD_S
                                ),
                            )
                        )

                        heartbeat_value = (
                            rearm_result.heartbeat_value
                        )
                        last_heartbeat_write_time = (
                            time.monotonic()
                        )
                        state = rearm_result.state

                        await publish_runtime_state(
                            gateway_variables=gateway_variables,
                            state=state,
                        )

                        last_enable_command = False
                        boundary_reference_dac = 0
                        last_gateway_applied_dac = 0
                        dac_boundary_limited = False
                        watchdog_fault_reported = False

                        logging.info(
                            (
                                "PLC watchdog safely re-armed. "
                                "Gateway commands remain reset to zero."
                            )
                        )

                    enable_command = bool(
                        await gateway_variables.enable_command.read_value()
                    )
                    dac_command = int(
                        await gateway_variables.dac_command.read_value()
                    )

                    # Confirm the current PLC command DAC as the limiter
                    # reference before selecting the next write.
                    boundary_reference_dac = int(state.dac)

                    boundary_result = limit_dac_boundary_step(
                        requested_dac=dac_command,
                        reference_dac=boundary_reference_dac,
                        maximum_delta=DAC_BOUNDARY_MAX_DELTA,
                        dac_min=DAC_BOUNDARY_MIN,
                        dac_max=DAC_BOUNDARY_MAX,
                    )
                    dac_boundary_limited = (
                        boundary_result.limited
                    )

                    # Disable first so the physical PLC gate closes before
                    # any DAC ramp-down operation.
                    if (
                        not enable_command
                        and state.enable
                    ):
                        await write_value_only(
                            br_connection.enable_node,
                            False,
                            ua.VariantType.Boolean,
                        )
                        last_enable_command = False
                        logging.info(
                            "Written to B&R PLC: Enable = False"
                        )

                    if (
                        boundary_result.applied_dac
                        != boundary_reference_dac
                    ):
                        await write_value_only(
                            br_connection.dac_node,
                            boundary_result.applied_dac,
                            ua.VariantType.Int16,
                        )
                        boundary_reference_dac = (
                            boundary_result.applied_dac
                        )
                        last_gateway_applied_dac = (
                            boundary_result.applied_dac
                        )
                        logging.info(
                            (
                                "Written to B&R PLC: DAC requested=%s, "
                                "applied=%s, delta=%s, limited=%s"
                            ),
                            dac_command,
                            boundary_result.applied_dac,
                            boundary_result.applied_delta,
                            boundary_result.limited,
                        )
                    else:
                        last_gateway_applied_dac = (
                            boundary_reference_dac
                        )

                    # Enable only after the DAC step for this cycle has been
                    # successfully written.
                    if (
                        enable_command
                        and not state.enable
                    ):
                        await write_value_only(
                            br_connection.enable_node,
                            True,
                            ua.VariantType.Boolean,
                        )
                        last_enable_command = True
                        logging.info(
                            "Written to B&R PLC: Enable = True"
                        )

                    if (
                        elapsed_time_s - last_log_time
                        >= LOG_PERIOD_S
                    ):
                        last_log_time = elapsed_time_s

                        level_raw = float(state.raw_level)
                        level_cm = raw_level_to_cm(level_raw)

                        filtered_level_gateway_cm = (
                            update_filtered_value(
                                previous_filtered=(
                                    filtered_level_gateway_cm
                                ),
                                current_value=level_cm,
                                alpha=PV_FILTER_ALPHA,
                                reset=PV_FILTER_RESET,
                            )
                        )

                        error_cm = (
                            PI_SETPOINT_CM - level_cm
                        )
                        filtered_error_gateway_cm = (
                            PI_SETPOINT_CM
                            - filtered_level_gateway_cm
                        )

                        mv_gateway_percent = dac_to_percent(
                            dac_command
                        )
                        mv_gateway_applied_percent = (
                            dac_to_percent(
                                last_gateway_applied_dac
                            )
                        )
                        mv_br_percent = dac_to_percent(
                            state.dac
                        )

                        csv_writer.writerow([
                            datetime.now().isoformat(
                                timespec="milliseconds"
                            ),
                            round(elapsed_time_s, 3),
                            round(level_raw, 6),
                            round(level_cm, 6),
                            round(
                                filtered_level_gateway_cm,
                                6,
                            ),
                            PI_SETPOINT_RAW_EQUIVALENT,
                            PI_SETPOINT_CM,
                            round(error_cm, 6),
                            round(
                                filtered_error_gateway_cm,
                                6,
                            ),
                            dac_command,
                            state.dac,
                            round(
                                mv_gateway_percent,
                                6,
                            ),
                            round(
                                mv_br_percent,
                                6,
                            ),
                            enable_command,
                            state.enable,
                            PI_KP,
                            PI_KI,
                            PI_KD,
                            PI_SAMPLING_TIME_S,
                            PI_MANUAL_MODE,
                            PI_MANUAL_OUTPUT,
                            PI_RESET,
                            PV_FILTER_ALPHA,
                            PV_FILTER_RESET,
                            DAC_LIMITER_MAX_DELTA,
                            DAC_LIMITER_MIN,
                            DAC_LIMITER_MAX,
                            DAC_LIMITER_RESET,
                            LEVEL_SCALE,
                            (
                                "PI/PID and SAFE_DAC_RATE_LIMITER "
                                "execute in 4diac FORTE. The gateway "
                                "applies a final DAC boundary limit and "
                                "requires a healthy PLC watchdog before "
                                "forwarding commands. Level scaling "
                                "remains provisional."
                            ),
                            communication_state,
                            reconnection_count,
                            last_gateway_applied_dac,
                            round(
                                mv_gateway_applied_percent,
                                6,
                            ),
                            dac_boundary_limited,
                            DAC_BOUNDARY_MAX_DELTA,
                            heartbeat_value,
                            state.safety_reset,
                            state.watchdog_healthy,
                            state.watchdog_tripped,
                            state.applied_enable,
                            state.applied_dac,
                            commands_permitted,
                        ])

                        if (
                            communication_state
                            == COMMUNICATION_STATE_RECONNECTED
                        ):
                            communication_state = (
                                COMMUNICATION_STATE_CONNECTED
                            )

                        csv_file.flush()

                        logging.info(
                            (
                                "CSV: t=%.1fs | Raw level=%s | "
                                "DAC requested=%s | DAC gateway=%s | "
                                "DAC PLC=%s | AppliedDAC=%s | "
                                "Enable command=%s | Enable PLC=%s | "
                                "AppliedEnable=%s | Healthy=%s | "
                                "Tripped=%s"
                            ),
                            elapsed_time_s,
                            state.raw_level,
                            dac_command,
                            last_gateway_applied_dac,
                            state.dac,
                            state.applied_dac,
                            enable_command,
                            state.enable,
                            state.applied_enable,
                            state.watchdog_healthy,
                            state.watchdog_tripped,
                        )

                except Exception as error:
                    logging.exception(
                        (
                            "PLC cycle failed (%s). The gateway "
                            "will discard commands and reconnect."
                        ),
                        connection_error_text(error),
                    )

                    try:
                        await write_safe_plc_commands(
                            br_connection
                        )
                    except Exception:
                        pass

                    await close_br_connection(
                        br_connection
                    )
                    br_connection = None

                    await publish_gateway_disconnected_state(
                        gateway_variables
                    )

                    last_enable_command = False
                    boundary_reference_dac = 0
                    last_gateway_applied_dac = 0
                    dac_boundary_limited = False
                    watchdog_fault_reported = True
                    next_reconnect_time = (
                        time.monotonic()
                        + BR_RECONNECT_INTERVAL_S
                    )

                await asyncio.sleep(
                    GATEWAY_CYCLE_TIME_S
                )

    except KeyboardInterrupt:
        logging.info("Gateway stopped by the user.")

    except Exception:
        logging.exception("Fatal gateway error.")

    finally:
        if br_connection is not None:
            try:
                await write_safe_plc_commands(
                    br_connection
                )
                logging.info(
                    "Final safe PLC commands were written."
                )
            except Exception:
                logging.exception(
                    (
                        "Could not write final safe commands. "
                        "The PLC watchdog remains the fallback."
                    )
                )

        if csv_file is not None:
            try:
                csv_file.close()
                logging.info(
                    "CSV file closed: %s",
                    CSV_PATH,
                )
            except Exception:
                logging.exception(
                    "Could not close the CSV file correctly."
                )

        await close_br_connection(br_connection)
        logging.info(
            "Disconnected from the B&R OPC UA server."
        )


if __name__ == "__main__":
    asyncio.run(main())
