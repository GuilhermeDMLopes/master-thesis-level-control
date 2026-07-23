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
    CSV_PATH,
    DAC_LIMITER_MAX,
    DAC_LIMITER_MAX_DELTA,
    DAC_LIMITER_MIN,
    DAC_LIMITER_RESET,
    GATEWAY_CYCLE_TIME_S,
    GATEWAY_ENDPOINT,
    GATEWAY_NAMESPACE_URI,
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

from gateway_processing import (
    dac_to_percent,
    raw_level_to_cm,
    update_filtered_value,
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

    writer.writerow([
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
    ])

    csv_file.flush()
    return csv_file, writer


# ============================================================
# GATEWAY
# ============================================================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    br_client = Client(BR_ENDPOINT)
    csv_file = None
    filtered_level_gateway_cm: float | None = None

    try:
        logging.info("Connecting to the B&R OPC UA server: %s", BR_ENDPOINT)
        await br_client.connect()
        logging.info("Connected to the B&R OPC UA server.")

        br_level_node = br_client.get_node(BR_LEVEL_NODE_ID)
        br_enable_node = br_client.get_node(BR_ENABLE_NODE_ID)
        br_dac_node = br_client.get_node(BR_DAC_NODE_ID)

        initial_raw_level = await br_level_node.read_value()
        initial_enable = await br_enable_node.read_value()
        initial_dac = await br_dac_node.read_value()

        logging.info("Initial values read from the B&R PLC:")
        logging.info("  Raw level = %s", initial_raw_level)
        logging.info("  Level     = %.3f cm", raw_level_to_cm(initial_raw_level))
        logging.info("  Enable    = %s", initial_enable)
        logging.info("  DAC       = %s", initial_dac)

        filtered_level_gateway_cm = raw_level_to_cm(initial_raw_level)

        server = Server()
        await server.init()
        server.set_endpoint(GATEWAY_ENDPOINT)
        server.set_server_name("B&R to 4diac OPC UA Gateway")

        namespace_index = await server.register_namespace(GATEWAY_NAMESPACE_URI)

        gateway_object = await server.nodes.objects.add_object(
            namespace_index,
            "BR_Gateway",
        )

        # These NodeIds are preserved for compatibility with the existing
        # 4diac application.
        level_variable = await gateway_object.add_variable(
            ua.NodeId("Nivel", namespace_index),
            "Nivel",
            ua.Variant(float(initial_raw_level), ua.VariantType.Double),
        )

        enable_variable = await gateway_object.add_variable(
            ua.NodeId("Enable", namespace_index),
            "Enable",
            ua.Variant(bool(initial_enable), ua.VariantType.Boolean),
        )

        dac_variable = await gateway_object.add_variable(
            ua.NodeId("DAC", namespace_index),
            "DAC",
            ua.Variant(int(initial_dac), ua.VariantType.Int16),
        )

        await enable_variable.set_writable()
        await dac_variable.set_writable()

        last_enable_command = bool(initial_enable)
        last_dac_command = int(initial_dac)

        csv_file, csv_writer = open_csv_logger(CSV_PATH)
        logging.info("Experiment CSV created at: %s", CSV_PATH)

        start_time = time.monotonic()
        last_log_time = 0.0

        async with server:
            logging.info("Gateway OPC UA server running at: %s", GATEWAY_ENDPOINT)
            logging.info("Gateway namespace registered as ns=%s", namespace_index)
            logging.info("NodeIds expected by 4diac FORTE:")
            logging.info(
                "  ns=%s;s=Nivel  [Double/LREAL, raw level]",
                namespace_index,
            )
            logging.info("  ns=%s;s=Enable [Boolean]", namespace_index)
            logging.info("  ns=%s;s=DAC    [Int16]", namespace_index)

            while True:
                try:
                    elapsed_time_s = time.monotonic() - start_time

                    raw_level_value = await br_level_node.read_value()
                    await level_variable.write_value(
                        ua.Variant(
                            float(raw_level_value),
                            ua.VariantType.Double,
                        )
                    )

                    enable_command = bool(await enable_variable.read_value())
                    dac_command = int(await dac_variable.read_value())

                    # This baseline preserves the current behavior. Command and
                    # feedback separation will be reviewed in a later stage.
                    if enable_command != last_enable_command:
                        await write_value_only(
                            br_enable_node,
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
                            br_dac_node,
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

                        confirmed_raw_level = await br_level_node.read_value()
                        confirmed_enable = bool(
                            await br_enable_node.read_value()
                        )
                        confirmed_dac = int(await br_dac_node.read_value())

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
                            datetime.now().isoformat(timespec="milliseconds"),
                            round(elapsed_time_s, 3),
                            level_raw,
                            level_cm,
                            filtered_level_gateway_cm,
                            PI_SETPOINT_RAW_EQUIVALENT,
                            PI_SETPOINT_CM,
                            error_cm,
                            filtered_error_gateway_cm,
                            dac_command,
                            confirmed_dac,
                            mv_gateway_percent,
                            mv_br_percent,
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
                                "Baseline gateway with the PI/PID, PV filter, "
                                "and DAC rate limiter implemented in 4diac "
                                "FORTE. The gateway filter is used only for "
                                "offline analysis."
                            ),
                        ])

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

                except Exception:
                    logging.exception("Error during the gateway cycle.")

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

        try:
            await br_client.disconnect()
            logging.info("Disconnected from the B&R OPC UA server.")
        except Exception:
            logging.exception(
                "Could not disconnect from the B&R OPC UA server cleanly."
            )


if __name__ == "__main__":
    asyncio.run(main())
