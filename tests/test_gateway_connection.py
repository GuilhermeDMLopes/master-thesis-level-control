from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest
from asyncua import ua

from gateway_connection import (
    BrConnection,
    close_br_connection,
    open_br_connection,
    read_br_runtime_state,
)
from gateway_opcua import (
    connection_error_text,
    synchronize_after_reconnection,
)


@dataclass
class FakeNode:
    value: Any

    async def read_value(self) -> Any:
        return self.value


@dataclass
class FakeClient:
    endpoint: str
    nodes: dict[str, FakeNode]
    connect_error: Exception | None = None
    disconnect_error: Exception | None = None
    connect_calls: int = 0
    disconnect_calls: int = 0

    async def connect(self) -> None:
        self.connect_calls += 1

        if self.connect_error is not None:
            raise self.connect_error

    async def disconnect(self) -> None:
        self.disconnect_calls += 1

        if self.disconnect_error is not None:
            raise self.disconnect_error

    def get_node(self, node_id: str) -> FakeNode:
        return self.nodes[node_id]


@dataclass
class FakeGatewayVariable:
    value: Any = None
    written_variants: list[ua.Variant] = field(default_factory=list)

    async def write_value(self, value: ua.Variant) -> None:
        self.written_variants.append(value)
        self.value = value.Value


def assert_variant(
    variant: ua.Variant,
    *,
    expected_value: Any,
    expected_type: ua.VariantType,
) -> None:
    assert variant.Value == expected_value
    assert variant.VariantType == expected_type


def create_fake_client(
    *,
    connect_error: Exception | None = None,
    disconnect_error: Exception | None = None,
) -> FakeClient:
    return FakeClient(
        endpoint="opc.tcp://127.0.0.1:4842",
        nodes={
            "level": FakeNode(14000.0),
            "enable": FakeNode(False),
            "dac": FakeNode(0),
            "heartbeat": FakeNode(10),
            "safety_reset": FakeNode(False),
            "watchdog_healthy": FakeNode(True),
            "watchdog_tripped": FakeNode(False),
            "applied_enable": FakeNode(False),
            "applied_dac": FakeNode(0),
        },
        connect_error=connect_error,
        disconnect_error=disconnect_error,
    )


def connection_arguments(
    *,
    client_factory: Any,
) -> dict[str, Any]:
    return {
        "endpoint": "opc.tcp://127.0.0.1:4842",
        "level_node_id": "level",
        "enable_node_id": "enable",
        "dac_node_id": "dac",
        "heartbeat_node_id": "heartbeat",
        "safety_reset_node_id": "safety_reset",
        "watchdog_healthy_node_id": "watchdog_healthy",
        "watchdog_tripped_node_id": "watchdog_tripped",
        "applied_enable_node_id": "applied_enable",
        "applied_dac_node_id": "applied_dac",
        "client_factory": client_factory,
    }


def build_connection(client: FakeClient) -> BrConnection:
    return BrConnection(
        client=client,
        level_node=client.nodes["level"],
        enable_node=client.nodes["enable"],
        dac_node=client.nodes["dac"],
        heartbeat_node=client.nodes["heartbeat"],
        safety_reset_node=client.nodes["safety_reset"],
        watchdog_healthy_node=client.nodes["watchdog_healthy"],
        watchdog_tripped_node=client.nodes["watchdog_tripped"],
        applied_enable_node=client.nodes["applied_enable"],
        applied_dac_node=client.nodes["applied_dac"],
        raw_level=client.nodes["level"].value,
        enable=client.nodes["enable"].value,
        dac=client.nodes["dac"].value,
        heartbeat=client.nodes["heartbeat"].value,
        safety_reset=client.nodes["safety_reset"].value,
        watchdog_healthy=client.nodes["watchdog_healthy"].value,
        watchdog_tripped=client.nodes["watchdog_tripped"].value,
        applied_enable=client.nodes["applied_enable"].value,
        applied_dac=client.nodes["applied_dac"].value,
    )


def create_gateway_variables() -> Any:
    return SimpleNamespace(
        level=FakeGatewayVariable(),
        enable_command=FakeGatewayVariable(True),
        dac_command=FakeGatewayVariable(9000),
        enable_feedback=FakeGatewayVariable(),
        dac_feedback=FakeGatewayVariable(),
        watchdog_healthy=FakeGatewayVariable(),
        watchdog_tripped=FakeGatewayVariable(),
        applied_enable=FakeGatewayVariable(),
        applied_dac=FakeGatewayVariable(),
    )


def test_open_br_connection_creates_fresh_client_and_reads_state() -> None:
    clients: list[FakeClient] = []

    def client_factory(endpoint: str) -> FakeClient:
        client = create_fake_client()
        client.endpoint = endpoint
        clients.append(client)
        return client

    connection = asyncio.run(
        open_br_connection(
            **connection_arguments(
                client_factory=client_factory
            )
        )
    )

    assert len(clients) == 1
    assert clients[0].connect_calls == 1
    assert connection.client is clients[0]
    assert connection.raw_level == 14000.0
    assert connection.enable is False
    assert connection.dac == 0
    assert connection.heartbeat == 10
    assert connection.safety_reset is False
    assert connection.watchdog_healthy is True
    assert connection.watchdog_tripped is False
    assert connection.applied_enable is False
    assert connection.applied_dac == 0


def test_open_br_connection_cleans_up_failed_client() -> None:
    client = create_fake_client(
        connect_error=ConnectionError("offline"),
    )

    with pytest.raises(ConnectionError, match="offline"):
        asyncio.run(
            open_br_connection(
                **connection_arguments(
                    client_factory=lambda _: client
                )
            )
        )

    assert client.connect_calls == 1
    assert client.disconnect_calls == 1


def test_read_br_runtime_state_reads_watchdog_and_applied_outputs() -> None:
    client = create_fake_client()
    client.nodes["level"].value = 451
    client.nodes["heartbeat"].value = 615
    client.nodes["watchdog_healthy"].value = False
    client.nodes["watchdog_tripped"].value = True

    state = asyncio.run(
        read_br_runtime_state(
            build_connection(client)
        )
    )

    assert state.raw_level == 451.0
    assert state.enable is False
    assert state.dac == 0
    assert state.heartbeat == 615
    assert state.safety_reset is False
    assert state.watchdog_healthy is False
    assert state.watchdog_tripped is True
    assert state.applied_enable is False
    assert state.applied_dac == 0


def test_close_br_connection_ignores_cleanup_failure() -> None:
    client = create_fake_client(
        disconnect_error=ConnectionError("already closed"),
    )

    asyncio.run(
        close_br_connection(
            build_connection(client)
        )
    )

    assert client.disconnect_calls == 1


def test_synchronize_after_reconnection_discards_offline_commands() -> None:
    client = create_fake_client()
    client.nodes["level"].value = 16000.0
    variables = create_gateway_variables()

    result = asyncio.run(
        synchronize_after_reconnection(
            connection=build_connection(client),
            gateway_variables=variables,
        )
    )

    assert result.raw_level == 16000.0
    assert result.enable is False
    assert result.dac == 0
    assert result.watchdog_healthy is True
    assert result.watchdog_tripped is False

    assert_variant(
        variables.level.written_variants[0],
        expected_value=16000.0,
        expected_type=ua.VariantType.Double,
    )
    assert_variant(
        variables.enable_command.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        variables.dac_command.written_variants[0],
        expected_value=0,
        expected_type=ua.VariantType.Int16,
    )
    assert_variant(
        variables.watchdog_healthy.written_variants[0],
        expected_value=True,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        variables.watchdog_tripped.written_variants[0],
        expected_value=False,
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


def test_synchronize_after_reconnection_rejects_nonzero_applied_output() -> None:
    client = create_fake_client()
    client.nodes["applied_dac"].value = 12000

    with pytest.raises(
        RuntimeError,
        match="not safe",
    ):
        asyncio.run(
            synchronize_after_reconnection(
                connection=build_connection(client),
                gateway_variables=create_gateway_variables(),
            )
        )


@pytest.mark.parametrize(
    "error, expected_text",
    [
        (
            ConnectionError("Connection is closed"),
            "ConnectionError: Connection is closed",
        ),
        (
            ConnectionError(),
            "ConnectionError",
        ),
    ],
)
def test_connection_error_text(
    error: BaseException,
    expected_text: str,
) -> None:
    assert connection_error_text(error) == expected_text
