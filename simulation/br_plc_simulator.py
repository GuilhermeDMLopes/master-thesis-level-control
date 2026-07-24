from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from asyncua import Server, ua


# ============================================================
# SIMULATOR CONFIGURATION
# ============================================================

SIMULATOR_ENDPOINT = "opc.tcp://0.0.0.0:4842"
SIMULATOR_SERVER_NAME = "B&R PLC OPC UA Simulator"

# The real PLC exposes the process variables in namespace 6.
TARGET_NAMESPACE_INDEX = 6

SIMULATOR_NAMESPACE_URI = "urn:br-plc-simulator"

BR_LEVEL_NODE_IDENTIFIER = "::Program:Nivel"
BR_ENABLE_NODE_IDENTIFIER = "::Program:Enable"
BR_DAC_NODE_IDENTIFIER = "::Program:DAC"

CYCLE_TIME_S = 0.1

INITIAL_LEVEL_RAW = 10000.0
INITIAL_ENABLE = False
INITIAL_DAC = 0

# Simple deterministic level profile used only to validate communication.
#
# This is not a physical tank model. The dynamic plant simulator will be
# implemented later.
LEVEL_PROFILE = (
    (0.0, 10000.0),
    (10.0, 12000.0),
    (20.0, 14000.0),
    (30.0, 16000.0),
    (40.0, 14000.0),
    (50.0, 12000.0),
)

LEVEL_PROFILE_PERIOD_S = 60.0


@dataclass(frozen=True)
class SimulatorVariables:
    level: object
    enable: object
    dac: object


async def register_namespace_six(
    server: Server,
) -> int:
    """
    Register placeholder namespaces until the simulator namespace is
    assigned index 6.

    The production gateway accesses the PLC using fixed namespace-6
    NodeIds, so the simulator must reproduce that exact contract.
    """
    for expected_index in range(2, TARGET_NAMESPACE_INDEX):
        registered_index = await server.register_namespace(
            f"urn:br-plc-simulator:reserved:{expected_index}"
        )

        if registered_index != expected_index:
            raise RuntimeError(
                "Unexpected namespace registration order: "
                f"expected {expected_index}, "
                f"received {registered_index}."
            )

    namespace_index = await server.register_namespace(
        SIMULATOR_NAMESPACE_URI
    )

    if namespace_index != TARGET_NAMESPACE_INDEX:
        raise RuntimeError(
            "The simulator namespace was not assigned index 6: "
            f"received {namespace_index}."
        )

    return namespace_index


async def create_simulator_variables(
    server: Server,
    namespace_index: int,
) -> SimulatorVariables:
    """
    Create the OPC UA variables that reproduce the B&R PLC interface.
    """
    program_object = await server.nodes.objects.add_object(
        namespace_index,
        "Program",
    )

    level_variable = await program_object.add_variable(
        ua.NodeId(
            BR_LEVEL_NODE_IDENTIFIER,
            namespace_index,
        ),
        "Nivel",
        ua.Variant(
            INITIAL_LEVEL_RAW,
            ua.VariantType.Double,
        ),
    )

    enable_variable = await program_object.add_variable(
        ua.NodeId(
            BR_ENABLE_NODE_IDENTIFIER,
            namespace_index,
        ),
        "Enable",
        ua.Variant(
            INITIAL_ENABLE,
            ua.VariantType.Boolean,
        ),
    )

    dac_variable = await program_object.add_variable(
        ua.NodeId(
            BR_DAC_NODE_IDENTIFIER,
            namespace_index,
        ),
        "DAC",
        ua.Variant(
            INITIAL_DAC,
            ua.VariantType.Int16,
        ),
    )

    # The gateway writes these two command variables.
    await enable_variable.set_writable()
    await dac_variable.set_writable()

    # Nivel remains read only for external clients. The simulator updates
    # it internally using the deterministic profile below.
    return SimulatorVariables(
        level=level_variable,
        enable=enable_variable,
        dac=dac_variable,
    )


def level_from_profile(elapsed_s: float) -> float:
    """
    Return the level value associated with the current profile interval.
    """
    profile_time = elapsed_s % LEVEL_PROFILE_PERIOD_S
    current_level = LEVEL_PROFILE[0][1]

    for start_time_s, level_raw in LEVEL_PROFILE:
        if profile_time < start_time_s:
            break

        current_level = level_raw

    return current_level


async def run_simulator() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    server = Server()
    await server.init()

    server.set_endpoint(SIMULATOR_ENDPOINT)
    server.set_server_name(SIMULATOR_SERVER_NAME)

    namespace_index = await register_namespace_six(server)

    variables = await create_simulator_variables(
        server=server,
        namespace_index=namespace_index,
    )

    last_enable = INITIAL_ENABLE
    last_dac = INITIAL_DAC
    last_level = INITIAL_LEVEL_RAW

    started_at = time.monotonic()

    async with server:
        logging.info(
            "B&R PLC simulator running at %s",
            SIMULATOR_ENDPOINT,
        )

        logging.info(
            "Namespace index: %s",
            namespace_index,
        )

        logging.info(
            "Level  NodeId: ns=%s;s=%s",
            namespace_index,
            BR_LEVEL_NODE_IDENTIFIER,
        )

        logging.info(
            "Enable NodeId: ns=%s;s=%s",
            namespace_index,
            BR_ENABLE_NODE_IDENTIFIER,
        )

        logging.info(
            "DAC    NodeId: ns=%s;s=%s",
            namespace_index,
            BR_DAC_NODE_IDENTIFIER,
        )

        while True:
            try:
                elapsed_s = time.monotonic() - started_at

                level_raw = level_from_profile(elapsed_s)

                if level_raw != last_level:
                    await variables.level.write_value(
                        ua.Variant(
                            level_raw,
                            ua.VariantType.Double,
                        )
                    )

                    last_level = level_raw

                    logging.info(
                        "Simulated level changed: raw=%.1f, cm=%.2f",
                        level_raw,
                        level_raw / 1000.0,
                    )

                enable_value = bool(
                    await variables.enable.read_value()
                )

                dac_value = int(
                    await variables.dac.read_value()
                )

                if enable_value != last_enable:
                    last_enable = enable_value

                    logging.info(
                        "Gateway command received: Enable=%s",
                        enable_value,
                    )

                if dac_value != last_dac:
                    last_dac = dac_value

                    logging.info(
                        "Gateway command received: DAC=%s",
                        dac_value,
                    )

            except Exception:
                logging.exception(
                    "Error during the PLC simulator cycle."
                )

            await asyncio.sleep(CYCLE_TIME_S)


def main() -> None:
    try:
        asyncio.run(run_simulator())
    except KeyboardInterrupt:
        logging.info(
            "B&R PLC simulator stopped by the user."
        )


if __name__ == "__main__":
    main()
