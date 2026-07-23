from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asyncua import ua

from gateway_config import (
    GATEWAY_DAC_FEEDBACK_NODE_ID,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
)


@dataclass(frozen=True)
class GatewayVariables:
    """
    References to the OPC UA variables exposed by the gateway server.

    The command variables are writable by OPC UA clients.
    The process and feedback variables remain read only for clients.
    """

    level: Any
    enable_command: Any
    dac_command: Any
    enable_feedback: Any
    dac_feedback: Any


async def create_gateway_variables(
    gateway_object: Any,
    namespace_index: int,
    initial_raw_level: Any,
    initial_enable: Any,
    initial_dac: Any,
) -> GatewayVariables:
    """
    Create the OPC UA variables exposed by the Python gateway.

    The legacy NodeIds are preserved for compatibility with the
    current 4diac FORTE application:

        Nivel
        Enable
        DAC

    The explicit read-only feedback NodeIds are:

        EnableFeedback
        DACFeedback
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

    # Only command variables may be written by OPC UA clients.
    await enable_command_variable.set_writable()
    await dac_command_variable.set_writable()

    return GatewayVariables(
        level=level_variable,
        enable_command=enable_command_variable,
        dac_command=dac_command_variable,
        enable_feedback=enable_feedback_variable,
        dac_feedback=dac_feedback_variable,
    )


async def publish_feedback_values(
    enable_feedback_variable: Any,
    dac_feedback_variable: Any,
    confirmed_enable: Any,
    confirmed_dac: Any,
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
