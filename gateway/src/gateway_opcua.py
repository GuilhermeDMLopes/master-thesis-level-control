from __future__ import annotations

import asyncio
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from asyncua import Client, Server, ua


from gateway_config import (
    BR_DAC_NODE_ID,
    BR_ENABLE_NODE_ID,
    BR_ENDPOINT,
    BR_LEVEL_NODE_ID,
    BR_RECONNECT_INTERVAL_S,
    CSV_PATH,
    DAC_LIMITER_MAX,
    DAC_LIMITER_MAX_DELTA,
    DAC_LIMITER_MIN,
    DAC_LIMITER_RESET,
    GATEWAY_CYCLE_TIME_S,
    GATEWAY_ENDPOINT,
    GATEWAY_NAMESPACE_URI,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
    GATEWAY_DAC_FEEDBACK_NODE_ID,
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
)

from gateway_connection import (
    BrConnection,
    close_br_connection,
    open_br_connection,
)

from gateway_interface import (
    create_gateway_variables,
    publish_feedback_values,
)

from gateway_processing import (
    dac_to_percent,
    raw_level_to_cm,
    update_filtered_value,
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
)


# ============================================================
# AUXILIARY FUNCTIONS
# ============================================================

async def write_value_only(
    node: Any,
    value: Any,
    variant_type: ua.VariantType,
) -> None:
    """
    Write only the Value attribute of an OPC UA node.

    Some industrial OPC UA servers reject writes that include status or
    timestamps. This helper creates a DataValue containing only the Variant.
    """
    variant = ua.Variant(value, variant_type)
    data_value = ua.DataValue(variant)
    await node.write_attribute(ua.AttributeIds.Value, data_value)


def open_csv_logger(file_path: Path) -> tuple[Any, csv.writer]:
    """Create the experiment CSV file and write its header."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    csv_file = file_path.open(mode="w", newline="", encoding="utf-8")
    writer = csv.writer(csv_file, delimiter=";")

    writer.writerow(CSV_HEADER)

    csv_file.flush()
    return csv_file, writer


# ============================================================
# GATEWAY
# ============================================================

async def synchronize_after_reconnection(
    *,
    connection: BrConnection,
    level_variable: Any,
    enable_command_variable: Any,
    dac_command_variable: Any,
    enable_feedback_variable: Any,
    dac_feedback_variable: Any,
) -> tuple[float, bool, int]:
    """
    Publish the confirmed PLC state and discard commands queued offline.

    Command variables are reset to values read from the PLC. Therefore, a
    command changed by a FORTE client while the PLC was disconnected is not
    transmitted automatically when communication returns.
    """
    raw_level = float(connection.raw_level)
    confirmed_enable = bool(connection.enable)
    confirmed_dac = int(connection.dac)

    await level_variable.write_value(
        ua.Variant(
            raw_level,
            ua.VariantType.Double,
        )
    )

    await enable_command_variable.write_value(
        ua.Variant(
            confirmed_enable,
            ua.VariantType.Boolean,
        )
    )

    await dac_command_variable.write_value(
        ua.Variant(
            confirmed_dac,
            ua.VariantType.Int16,
        )
    )

    await publish_feedback_values(
        enable_feedback_variable=enable_feedback_variable,
        dac_feedback_variable=dac_feedback_variable,
        confirmed_enable=confirmed_enable,
        confirmed_dac=confirmed_dac,
    )

    return raw_level, confirmed_enable, confirmed_dac


def connection_error_text(error: BaseException) -> str:
    """Return a concise connection error description for gateway logs."""
    detail = str(error).strip()

    if detail:
        return f"{error.__class__.__name__}: {detail}"

    return error.__class__.__name__


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    br_connection: BrConnection | None = None
    csv_file = None
    filtered_level_gateway_cm: float | None = None

    try:
        logging.info("Connecting to the B&R OPC UA server: %s", BR_ENDPOINT)

        br_connection = await open_br_connection(
            endpoint=BR_ENDPOINT,
            level_node_id=BR_LEVEL_NODE_ID,
            enable_node_id=BR_ENABLE_NODE_ID,
            dac_node_id=BR_DAC_NODE_ID,
        )

        logging.info("Connected to the B&R OPC UA server.")

        initial_raw_level = br_connection.raw_level
        initial_enable = br_connection.enable
        initial_dac = br_connection.dac

        logging.info("Initial values read from the B&R PLC:")
        logging.info("  Raw level = %s", initial_raw_level)
        logging.info(
            "  Level     = %.3f cm",
            raw_level_to_cm(initial_raw_level),
        )
        logging.info("  Enable    = %s", initial_enable)
        logging.info("  DAC       = %s", initial_dac)

        filtered_level_gateway_cm = raw_level_to_cm(initial_raw_level)

        server = Server()
        await server.init()
        server.set_endpoint(GATEWAY_ENDPOINT)
        server.set_server_name("B&R to 4diac OPC UA Gateway")

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
            initial_raw_level=initial_raw_level,
            initial_enable=initial_enable,
            initial_dac=initial_dac,
        )

        level_variable = gateway_variables.level
        enable_variable = gateway_variables.enable_command
        dac_variable = gateway_variables.dac_command
        enable_feedback_variable = gateway_variables.enable_feedback
        dac_feedback_variable = gateway_variables.dac_feedback

        last_enable_command = bool(initial_enable)
        last_dac_command = int(initial_dac)

        csv_file, csv_writer = open_csv_logger(CSV_PATH)
        logging.info("Experiment CSV created at: %s", CSV_PATH)

        start_time = time.monotonic()
        last_log_time = 0.0
        next_reconnect_time = 0.0
        reconnection_count = 0
        communication_state = COMMUNICATION_STATE_CONNECTED

        async with server:
            logging.info(
                "Gateway OPC UA server running at: %s",
                GATEWAY_ENDPOINT,
            )
            logging.info(
                "Gateway namespace registered as ns=%s",
                namespace_index,
            )
            logging.info("NodeIds expected by 4diac FORTE:")
            logging.info(
                "  ns=%s;s=Nivel  [Double/LREAL, raw level]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=Enable [Boolean, command]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=DAC    [Int16, command]",
                namespace_index,
            )
            logging.info(
                "  ns=%s;s=%s [Boolean, feedback, read only]",
                namespace_index,
                GATEWAY_ENABLE_FEEDBACK_NODE_ID,
            )
            logging.info(
                "  ns=%s;s=%s [Int16, feedback, read only]",
                namespace_index,
                GATEWAY_DAC_FEEDBACK_NODE_ID,
            )

            while True:
                elapsed_time_s = time.monotonic() - start_time

                if br_connection is None:
                    current_time = time.monotonic()

                    if current_time >= next_reconnect_time:
                        logging.info(
                            "Attempting to reconnect to the B&R OPC UA "
                            "server: %s",
                            BR_ENDPOINT,
                        )

                        try:
                            candidate_connection = await open_br_connection(
                                endpoint=BR_ENDPOINT,
                                level_node_id=BR_LEVEL_NODE_ID,
                                enable_node_id=BR_ENABLE_NODE_ID,
                                dac_node_id=BR_DAC_NODE_ID,
                            )

                        except (
                            ConnectionError,
                            OSError,
                            asyncio.TimeoutError,
                        ) as error:
                            next_reconnect_time = (
                                time.monotonic()
                                + BR_RECONNECT_INTERVAL_S
                            )

                            logging.warning(
                                (
                                    "Reconnection attempt failed (%s). "
                                    "Next attempt in %.1f seconds."
                                ),
                                connection_error_text(error),
                                BR_RECONNECT_INTERVAL_S,
                            )

                        except Exception:
                            next_reconnect_time = (
                                time.monotonic()
                                + BR_RECONNECT_INTERVAL_S
                            )

                            logging.exception(
                                (
                                    "Unexpected error while reconnecting to "
                                    "the B&R OPC UA server. Next attempt in "
                                    "%.1f seconds."
                                ),
                                BR_RECONNECT_INTERVAL_S,
                            )

                        else:
                            br_connection = candidate_connection

                            (
                                reconnected_raw_level,
                                last_enable_command,
                                last_dac_command,
                            ) = await synchronize_after_reconnection(
                                connection=br_connection,
                                level_variable=level_variable,
                                enable_command_variable=enable_variable,
                                dac_command_variable=dac_variable,
                                enable_feedback_variable=(
                                    enable_feedback_variable
                                ),
                                dac_feedback_variable=(
                                    dac_feedback_variable
                                ),
                            )

                            filtered_level_gateway_cm = raw_level_to_cm(
                                reconnected_raw_level
                            )
                            last_log_time = elapsed_time_s
                            reconnection_count += 1
                            communication_state = (
                                COMMUNICATION_STATE_RECONNECTED
                            )

                            logging.info(
                                "Reconnected to the B&R OPC UA server."
                            )
                            logging.info(
                                (
                                    "PLC communication restored: raw level=%s, "
                                    "Enable=%s, DAC=%s. Offline commands were "
                                    "discarded."
                                ),
                                reconnected_raw_level,
                                last_enable_command,
                                last_dac_command,
                            )

                    await asyncio.sleep(GATEWAY_CYCLE_TIME_S)
                    continue

                try:
                    raw_level_value = (
                        await br_connection.level_node.read_value()
                    )
                    await level_variable.write_value(
                        ua.Variant(
                            float(raw_level_value),
                            ua.VariantType.Double,
                        )
                    )

                    enable_command = bool(
                        await enable_variable.read_value()
                    )
                    dac_command = int(await dac_variable.read_value())

                    if enable_command != last_enable_command:
                        await write_value_only(
                            br_connection.enable_node,
                            enable_command,
                            ua.VariantType.Boolean,
                        )
                        last_enable_command = enable_command
                        logging.info(
                            "Written to B&R PLC: Enable = %s",
                            enable_command,
                        )

                    if dac_command != last_dac_command:
                        await write_value_only(
                            br_connection.dac_node,
                            dac_command,
                            ua.VariantType.Int16,
                        )
                        last_dac_command = dac_command
                        logging.info(
                            "Written to B&R PLC: DAC = %s",
                            dac_command,
                        )

                    if (elapsed_time_s - last_log_time) >= LOG_PERIOD_S:
                        last_log_time = elapsed_time_s

                        confirmed_raw_level = (
                            await br_connection.level_node.read_value()
                        )
                        confirmed_enable = bool(
                            await br_connection.enable_node.read_value()
                        )
                        confirmed_dac = int(
                            await br_connection.dac_node.read_value()
                        )

                        await publish_feedback_values(
                            enable_feedback_variable=(
                                enable_feedback_variable
                            ),
                            dac_feedback_variable=dac_feedback_variable,
                            confirmed_enable=confirmed_enable,
                            confirmed_dac=confirmed_dac,
                        )

                        level_raw = float(confirmed_raw_level)
                        level_cm = raw_level_to_cm(level_raw)

                        filtered_level_gateway_cm = update_filtered_value(
                            previous_filtered=filtered_level_gateway_cm,
                            current_value=level_cm,
                            alpha=PV_FILTER_ALPHA,
                            reset=PV_FILTER_RESET,
                        )

                        error_cm = PI_SETPOINT_CM - level_cm
                        filtered_error_gateway_cm = (
                            PI_SETPOINT_CM - filtered_level_gateway_cm
                        )

                        mv_gateway_percent = dac_to_percent(dac_command)
                        mv_br_percent = dac_to_percent(confirmed_dac)

                        csv_writer.writerow([
                            datetime.now().isoformat(
                                timespec="milliseconds"
                            ),
                            round(elapsed_time_s, 3),
                            round(level_raw, 6),
                            round(level_cm, 6),
                            round(filtered_level_gateway_cm, 6),
                            PI_SETPOINT_RAW_EQUIVALENT,
                            PI_SETPOINT_CM,
                            round(error_cm, 6),
                            round(filtered_error_gateway_cm, 6),
                            dac_command,
                            confirmed_dac,
                            round(mv_gateway_percent, 6),
                            round(mv_br_percent, 6),
                            enable_command,
                            confirmed_enable,
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
                                "Baseline gateway with the PI/PID, PV "
                                "filter, and DAC rate limiter implemented "
                                "in 4diac FORTE. The gateway filter is used "
                                "only for offline analysis."
                            ),
                            communication_state,
                            reconnection_count,
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
                                "CSV: t=%.1fs | Level=%.2f cm | "
                                "Filtered level=%.2f cm | Setpoint=%.2f cm | "
                                "Filtered error=%.2f cm | DAC command=%s | "
                                "DAC feedback=%s | Enable command=%s | "
                                "Enable feedback=%s"
                            ),
                            elapsed_time_s,
                            level_cm,
                            filtered_level_gateway_cm,
                            PI_SETPOINT_CM,
                            filtered_error_gateway_cm,
                            dac_command,
                            confirmed_dac,
                            enable_command,
                            confirmed_enable,
                        )

                except (
                    ConnectionError,
                    OSError,
                    asyncio.TimeoutError,
                ) as error:
                    logging.warning(
                        (
                            "B&R PLC connection lost (%s). The gateway "
                            "server remains active. Next reconnection "
                            "attempt in %.1f seconds."
                        ),
                        connection_error_text(error),
                        BR_RECONNECT_INTERVAL_S,
                    )

                    await close_br_connection(br_connection)
                    br_connection = None
                    next_reconnect_time = (
                        time.monotonic()
                        + BR_RECONNECT_INTERVAL_S
                    )

                except Exception:
                    logging.exception(
                        "Unexpected error during the gateway cycle."
                    )

                await asyncio.sleep(GATEWAY_CYCLE_TIME_S)

    except KeyboardInterrupt:
        logging.info("Gateway stopped by the user.")

    except Exception:
        logging.exception("Fatal gateway error.")

    finally:
        if csv_file is not None:
            try:
                csv_file.close()
                logging.info("CSV file closed: %s", CSV_PATH)
            except Exception:
                logging.exception("Could not close the CSV file correctly.")

        await close_br_connection(br_connection)
        logging.info("Disconnected from the B&R OPC UA server.")


if __name__ == "__main__":
    asyncio.run(main())
