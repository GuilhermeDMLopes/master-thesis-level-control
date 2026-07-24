from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from asyncua import ua

from gateway_config import (
    GATEWAY_DAC_FEEDBACK_NODE_ID,
    GATEWAY_ENABLE_FEEDBACK_NODE_ID,
)
from gateway_interface import (
    GatewayVariables,
    create_gateway_variables,
    publish_feedback_values,
)


@dataclass
class FakeVariable:
    """
    Minimal offline replacement for an asyncua variable node.
    """

    node_id: ua.NodeId
    browse_name: str
    initial_variant: ua.Variant
    writable_call_count: int = 0
    written_variants: list[ua.Variant] = field(
        default_factory=list
    )

    async def set_writable(self) -> None:
        self.writable_call_count += 1

    async def write_value(
        self,
        value: ua.Variant,
    ) -> None:
        self.written_variants.append(value)


@dataclass
class FakeGatewayObject:
    """
    Minimal offline replacement for the gateway OPC UA object.
    """

    variables: list[FakeVariable] = field(
        default_factory=list
    )

    async def add_variable(
        self,
        node_id: ua.NodeId,
        browse_name: str,
        initial_variant: ua.Variant,
    ) -> FakeVariable:
        variable = FakeVariable(
            node_id=node_id,
            browse_name=browse_name,
            initial_variant=initial_variant,
        )

        self.variables.append(variable)

        return variable


def create_test_variables(
    *,
    namespace_index: int = 2,
    initial_raw_level: Any = 14000,
    initial_enable: Any = True,
    initial_dac: Any = 3200,
) -> tuple[FakeGatewayObject, GatewayVariables]:
    gateway_object = FakeGatewayObject()

    variables = asyncio.run(
        create_gateway_variables(
            gateway_object=gateway_object,
            namespace_index=namespace_index,
            initial_raw_level=initial_raw_level,
            initial_enable=initial_enable,
            initial_dac=initial_dac,
        )
    )

    return gateway_object, variables


def assert_variant(
    variant: ua.Variant,
    *,
    expected_value: Any,
    expected_type: ua.VariantType,
) -> None:
    assert variant.Value == expected_value
    assert variant.VariantType == expected_type


def test_create_gateway_variables_creates_expected_nodes() -> None:
    namespace_index = 4

    gateway_object, _ = create_test_variables(
        namespace_index=namespace_index
    )

    assert [
        variable.browse_name
        for variable in gateway_object.variables
    ] == [
        "Nivel",
        "Enable",
        "DAC",
        GATEWAY_ENABLE_FEEDBACK_NODE_ID,
        GATEWAY_DAC_FEEDBACK_NODE_ID,
    ]

    assert [
        variable.node_id
        for variable in gateway_object.variables
    ] == [
        ua.NodeId("Nivel", namespace_index),
        ua.NodeId("Enable", namespace_index),
        ua.NodeId("DAC", namespace_index),
        ua.NodeId(
            GATEWAY_ENABLE_FEEDBACK_NODE_ID,
            namespace_index,
        ),
        ua.NodeId(
            GATEWAY_DAC_FEEDBACK_NODE_ID,
            namespace_index,
        ),
    ]


def test_create_gateway_variables_uses_expected_values_and_types() -> None:
    gateway_object, _ = create_test_variables(
        initial_raw_level=14500,
        initial_enable=False,
        initial_dac=6400,
    )

    expected_variants = [
        (14500.0, ua.VariantType.Double),
        (False, ua.VariantType.Boolean),
        (6400, ua.VariantType.Int16),
        (False, ua.VariantType.Boolean),
        (6400, ua.VariantType.Int16),
    ]

    for variable, (
        expected_value,
        expected_type,
    ) in zip(
        gateway_object.variables,
        expected_variants,
        strict=True,
    ):
        assert_variant(
            variable.initial_variant,
            expected_value=expected_value,
            expected_type=expected_type,
        )


def test_only_command_variables_are_client_writable() -> None:
    gateway_object, _ = create_test_variables()

    writable_call_counts = {
        variable.browse_name:
            variable.writable_call_count
        for variable in gateway_object.variables
    }

    assert writable_call_counts == {
        "Nivel": 0,
        "Enable": 1,
        "DAC": 1,
        GATEWAY_ENABLE_FEEDBACK_NODE_ID: 0,
        GATEWAY_DAC_FEEDBACK_NODE_ID: 0,
    }


def test_gateway_variables_references_created_nodes() -> None:
    gateway_object, variables = create_test_variables()

    assert variables.level is gateway_object.variables[0]
    assert variables.enable_command is gateway_object.variables[1]
    assert variables.dac_command is gateway_object.variables[2]
    assert variables.enable_feedback is gateway_object.variables[3]
    assert variables.dac_feedback is gateway_object.variables[4]


def test_publish_feedback_values_uses_confirmed_plc_values() -> None:
    _, variables = create_test_variables(
        initial_enable=True,
        initial_dac=1000,
    )

    asyncio.run(
        publish_feedback_values(
            enable_feedback_variable=(
                variables.enable_feedback
            ),
            dac_feedback_variable=variables.dac_feedback,
            confirmed_enable=False,
            confirmed_dac=8750,
        )
    )

    assert len(
        variables.enable_feedback.written_variants
    ) == 1

    assert len(
        variables.dac_feedback.written_variants
    ) == 1

    assert_variant(
        variables.enable_feedback.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )

    assert_variant(
        variables.dac_feedback.written_variants[0],
        expected_value=8750,
        expected_type=ua.VariantType.Int16,
    )

    assert variables.enable_command.written_variants == []
    assert variables.dac_command.written_variants == []


def test_publish_feedback_values_normalizes_python_types() -> None:
    _, variables = create_test_variables()

    asyncio.run(
        publish_feedback_values(
            enable_feedback_variable=(
                variables.enable_feedback
            ),
            dac_feedback_variable=variables.dac_feedback,
            confirmed_enable=1,
            confirmed_dac="2500",
        )
    )

    assert_variant(
        variables.enable_feedback.written_variants[0],
        expected_value=True,
        expected_type=ua.VariantType.Boolean,
    )

    assert_variant(
        variables.dac_feedback.written_variants[0],
        expected_value=2500,
        expected_type=ua.VariantType.Int16,
    )
