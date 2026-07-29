from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asyncua import ua

from gateway_config import (
    GATEWAY_APPLIED_DAC_NODE_ID,
    GATEWAY_APPLIED_ENABLE_NODE_ID,
    GATEWAY_DAC_FEEDBACK_NODE_ID,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
    GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
    GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
)


@dataclass(frozen=True)
class GatewayVariables:
    """
    References to the OPC UA variables exposed by the gateway server.

    Only Enable and DAC are writable by OPC UA clients. Process, command
    feedback, watchdog, and applied-output values remain read only.
    """

    level: Any
    enable_command: Any
    dac_command: Any
    enable_feedback: Any
    dac_feedback: Any
    watchdog_healthy: Any
    watchdog_tripped: Any
    applied_enable: Any
    applied_dac: Any


async def create_gateway_variables(
    gateway_object: Any,
    namespace_index: int,
    initial_raw_level: Any,
    initial_enable: Any,
    initial_dac: Any,
    initial_watchdog_healthy: Any = False,
    initial_watchdog_tripped: Any = True,
    initial_applied_enable: Any = False,
    initial_applied_dac: Any = 0,
) -> GatewayVariables:
    """
    Create the OPC UA variables exposed by the Python gateway.

    Legacy command NodeIds are preserved for the current FORTE application:

        Nivel
        Enable
        DAC

    Read-only PLC feedback and watchdog NodeIds are:

        EnableFeedback
        DACFeedback
        WatchdogHealthy
        WatchdogTripped
        AppliedEnable
        AppliedDAC
    """
    level_variable = await gateway_object.add_variable(
        ua.NodeId("Nivel", namespace_index),
        "Nivel",
        ua.Variant(
            float(initial_raw_level),
            ua.VariantType.Double,
        ),
    )

    enable_command_variable = await gateway_object.add_variable(
        ua.NodeId("Enable", namespace_index),
        "Enable",
        ua.Variant(
            bool(initial_enable),
            ua.VariantType.Boolean,
        ),
    )

    dac_command_variable = await gateway_object.add_variable(
        ua.NodeId("DAC", namespace_index),
        "DAC",
        ua.Variant(
            int(initial_dac),
            ua.VariantType.Int16,
        ),
    )

    enable_feedback_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_ENABLE_FEEDBACK_NODE_ID,
            namespace_index,
        ),
        GATEWAY_ENABLE_FEEDBACK_NODE_ID,
        ua.Variant(
            bool(initial_enable),
            ua.VariantType.Boolean,
        ),
    )

    dac_feedback_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_DAC_FEEDBACK_NODE_ID,
            namespace_index,
        ),
        GATEWAY_DAC_FEEDBACK_NODE_ID,
        ua.Variant(
            int(initial_dac),
            ua.VariantType.Int16,
        ),
    )

    watchdog_healthy_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
            namespace_index,
        ),
        GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
        ua.Variant(
            bool(initial_watchdog_healthy),
            ua.VariantType.Boolean,
        ),
    )

    watchdog_tripped_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
            namespace_index,
        ),
        GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
        ua.Variant(
            bool(initial_watchdog_tripped),
            ua.VariantType.Boolean,
        ),
    )

    applied_enable_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_APPLIED_ENABLE_NODE_ID,
            namespace_index,
        ),
        GATEWAY_APPLIED_ENABLE_NODE_ID,
        ua.Variant(
            bool(initial_applied_enable),
            ua.VariantType.Boolean,
        ),
    )

    applied_dac_variable = await gateway_object.add_variable(
        ua.NodeId(
            GATEWAY_APPLIED_DAC_NODE_ID,
            namespace_index,
        ),
        GATEWAY_APPLIED_DAC_NODE_ID,
        ua.Variant(
            int(initial_applied_dac),
            ua.VariantType.Int16,
        ),
    )

    # Only command variables may be written by OPC UA clients.
    await enable_command_variable.set_writable()
    await dac_command_variable.set_writable()

    return GatewayVariables(
        level=level_variable,
        enable_command=enable_command_variable,
        dac_command=dac_command_variable,
        enable_feedback=enable_feedback_variable,
        dac_feedback=dac_feedback_variable,
        watchdog_healthy=watchdog_healthy_variable,
        watchdog_tripped=watchdog_tripped_variable,
        applied_enable=applied_enable_variable,
        applied_dac=applied_dac_variable,
    )


async def publish_plc_feedback_values(
    *,
    enable_feedback_variable: Any,
    dac_feedback_variable: Any,
    watchdog_healthy_variable: Any,
    watchdog_tripped_variable: Any,
    applied_enable_variable: Any,
    applied_dac_variable: Any,
    confirmed_enable: Any,
    confirmed_dac: Any,
    watchdog_healthy: Any,
    watchdog_tripped: Any,
    applied_enable: Any,
    applied_dac: Any,
) -> None:
    """
    Publish values read directly from the B&R PLC.

    Command variables are deliberately not used as feedback sources.
    """
    await enable_feedback_variable.write_value(
        ua.Variant(
            bool(confirmed_enable),
            ua.VariantType.Boolean,
        )
    )

    await dac_feedback_variable.write_value(
        ua.Variant(
            int(confirmed_dac),
            ua.VariantType.Int16,
        )
    )

    await watchdog_healthy_variable.write_value(
        ua.Variant(
            bool(watchdog_healthy),
            ua.VariantType.Boolean,
        )
    )

    await watchdog_tripped_variable.write_value(
        ua.Variant(
            bool(watchdog_tripped),
            ua.VariantType.Boolean,
        )
    )

    await applied_enable_variable.write_value(
        ua.Variant(
            bool(applied_enable),
            ua.VariantType.Boolean,
        )
    )

    await applied_dac_variable.write_value(
        ua.Variant(
            int(applied_dac),
            ua.VariantType.Int16,
        )
    )


async def publish_disconnected_safe_state(
    *,
    enable_feedback_variable: Any,
    dac_feedback_variable: Any,
    watchdog_healthy_variable: Any,
    watchdog_tripped_variable: Any,
    applied_enable_variable: Any,
    applied_dac_variable: Any,
) -> None:
    """Publish a fail-closed state while PLC feedback is unavailable."""
    await publish_plc_feedback_values(
        enable_feedback_variable=enable_feedback_variable,
        dac_feedback_variable=dac_feedback_variable,
        watchdog_healthy_variable=watchdog_healthy_variable,
        watchdog_tripped_variable=watchdog_tripped_variable,
        applied_enable_variable=applied_enable_variable,
        applied_dac_variable=applied_dac_variable,
        confirmed_enable=False,
        confirmed_dac=0,
        watchdog_healthy=False,
        watchdog_tripped=True,
        applied_enable=False,
        applied_dac=0,
    )
