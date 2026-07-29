from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
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
from gateway_interface import (
    GatewayVariables,
    create_gateway_variables,
    publish_disconnected_safe_state,
    publish_plc_feedback_values,
)


@dataclass
class FakeVariable:
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
    initial_raw_level: Any = 237,
    initial_enable: Any = False,
    initial_dac: Any = 0,
    initial_watchdog_healthy: Any = True,
    initial_watchdog_tripped: Any = False,
    initial_applied_enable: Any = False,
    initial_applied_dac: Any = 0,
) -> tuple[FakeGatewayObject, GatewayVariables]:
    gateway_object = FakeGatewayObject()

    variables = asyncio.run(
        create_gateway_variables(
            gateway_object=gateway_object,
            namespace_index=namespace_index,
            initial_raw_level=initial_raw_level,
            initial_enable=initial_enable,
            initial_dac=initial_dac,
            initial_watchdog_healthy=(
                initial_watchdog_healthy
            ),
            initial_watchdog_tripped=(
                initial_watchdog_tripped
            ),
            initial_applied_enable=(
                initial_applied_enable
            ),
            initial_applied_dac=initial_applied_dac,
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


def test_legacy_create_gateway_variables_call_uses_safe_watchdog_defaults() -> None:
    gateway_object = FakeGatewayObject()

    asyncio.run(
        create_gateway_variables(
            gateway_object=gateway_object,
            namespace_index=2,
            initial_raw_level=14000,
            initial_enable=True,
            initial_dac=3200,
        )
    )

    variables = {
        variable.browse_name: variable
        for variable in gateway_object.variables
    }

    assert_variant(
        variables[
            GATEWAY_WATCHDOG_HEALTHY_NODE_ID
        ].initial_variant,
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )

    assert_variant(
        variables[
            GATEWAY_WATCHDOG_TRIPPED_NODE_ID
        ].initial_variant,
        expected_value=True,
        expected_type=ua.VariantType.Boolean,
    )

    assert_variant(
        variables[
            GATEWAY_APPLIED_ENABLE_NODE_ID
        ].initial_variant,
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )

    assert_variant(
        variables[
            GATEWAY_APPLIED_DAC_NODE_ID
        ].initial_variant,
        expected_value=0,
        expected_type=ua.VariantType.Int16,
    )


def test_create_gateway_variables_creates_expected_nodes() -> None:
    namespace_index = 4

    gateway_object, _ = create_test_variables(
        namespace_index=namespace_index
    )

    expected_names = [
        "Nivel",
        "Enable",
        "DAC",
        GATEWAY_ENABLE_FEEDBACK_NODE_ID,
        GATEWAY_DAC_FEEDBACK_NODE_ID,
        GATEWAY_WATCHDOG_HEALTHY_NODE_ID,
        GATEWAY_WATCHDOG_TRIPPED_NODE_ID,
        GATEWAY_APPLIED_ENABLE_NODE_ID,
        GATEWAY_APPLIED_DAC_NODE_ID,
    ]

    assert [
        variable.browse_name
        for variable in gateway_object.variables
    ] == expected_names

    assert [
        variable.node_id
        for variable in gateway_object.variables
    ] == [
        ua.NodeId(name, namespace_index)
        for name in expected_names
    ]


def test_create_gateway_variables_uses_expected_values_and_types() -> None:
    gateway_object, _ = create_test_variables(
        initial_raw_level=451,
        initial_enable=False,
        initial_dac=0,
        initial_watchdog_healthy=True,
        initial_watchdog_tripped=False,
        initial_applied_enable=False,
        initial_applied_dac=0,
    )

    expected_variants = [
        (451.0, ua.VariantType.Double),
        (False, ua.VariantType.Boolean),
        (0, ua.VariantType.Int16),
        (False, ua.VariantType.Boolean),
        (0, ua.VariantType.Int16),
        (True, ua.VariantType.Boolean),
        (False, ua.VariantType.Boolean),
        (False, ua.VariantType.Boolean),
        (0, ua.VariantType.Int16),
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
        GATEWAY_WATCHDOG_HEALTHY_NODE_ID: 0,
        GATEWAY_WATCHDOG_TRIPPED_NODE_ID: 0,
        GATEWAY_APPLIED_ENABLE_NODE_ID: 0,
        GATEWAY_APPLIED_DAC_NODE_ID: 0,
    }


def test_gateway_variables_references_created_nodes() -> None:
    gateway_object, variables = create_test_variables()

    assert variables.level is gateway_object.variables[0]
    assert variables.enable_command is gateway_object.variables[1]
    assert variables.dac_command is gateway_object.variables[2]
    assert variables.enable_feedback is gateway_object.variables[3]
    assert variables.dac_feedback is gateway_object.variables[4]
    assert variables.watchdog_healthy is gateway_object.variables[5]
    assert variables.watchdog_tripped is gateway_object.variables[6]
    assert variables.applied_enable is gateway_object.variables[7]
    assert variables.applied_dac is gateway_object.variables[8]


def test_publish_plc_feedback_values_uses_confirmed_values() -> None:
    _, variables = create_test_variables()

    asyncio.run(
        publish_plc_feedback_values(
            enable_feedback_variable=(
                variables.enable_feedback
            ),
            dac_feedback_variable=variables.dac_feedback,
            watchdog_healthy_variable=(
                variables.watchdog_healthy
            ),
            watchdog_tripped_variable=(
                variables.watchdog_tripped
            ),
            applied_enable_variable=(
                variables.applied_enable
            ),
            applied_dac_variable=variables.applied_dac,
            confirmed_enable=True,
            confirmed_dac=12000,
            watchdog_healthy=False,
            watchdog_tripped=True,
            applied_enable=False,
            applied_dac=0,
        )
    )

    expected = [
        (
            variables.enable_feedback,
            True,
            ua.VariantType.Boolean,
        ),
        (
            variables.dac_feedback,
            12000,
            ua.VariantType.Int16,
        ),
        (
            variables.watchdog_healthy,
            False,
            ua.VariantType.Boolean,
        ),
        (
            variables.watchdog_tripped,
            True,
            ua.VariantType.Boolean,
        ),
        (
            variables.applied_enable,
            False,
            ua.VariantType.Boolean,
        ),
        (
            variables.applied_dac,
            0,
            ua.VariantType.Int16,
        ),
    ]

    for variable, value, variant_type in expected:
        assert_variant(
            variable.written_variants[0],
            expected_value=value,
            expected_type=variant_type,
        )

    assert variables.enable_command.written_variants == []
    assert variables.dac_command.written_variants == []


def test_disconnected_state_is_fail_closed() -> None:
    _, variables = create_test_variables()

    asyncio.run(
        publish_disconnected_safe_state(
            enable_feedback_variable=(
                variables.enable_feedback
            ),
            dac_feedback_variable=variables.dac_feedback,
            watchdog_healthy_variable=(
                variables.watchdog_healthy
            ),
            watchdog_tripped_variable=(
                variables.watchdog_tripped
            ),
            applied_enable_variable=(
                variables.applied_enable
            ),
            applied_dac_variable=variables.applied_dac,
        )
    )

    assert_variant(
        variables.watchdog_healthy.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        variables.watchdog_tripped.written_variants[0],
        expected_value=True,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        variables.applied_enable.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        variables.applied_dac.written_variants[0],
        expected_value=0,
        expected_type=ua.VariantType.Int16,
    )
