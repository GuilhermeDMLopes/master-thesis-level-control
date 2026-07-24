from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest
from asyncua import ua

from gateway_connection import (
    BrConnection,
    close_br_connection,
    open_br_connection,
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
    written_variants: list[ua.Variant] = field(default_factory=list)

    async def write_value(self, value: ua.Variant) -> None:
        self.written_variants.append(value)


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
            "enable": FakeNode(True),
            "dac": FakeNode(2500),
        },
        connect_error=connect_error,
        disconnect_error=disconnect_error,
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
            endpoint="opc.tcp://127.0.0.1:4842",
            level_node_id="level",
            enable_node_id="enable",
            dac_node_id="dac",
            client_factory=client_factory,
        )
    )

    assert len(clients) == 1
    assert clients[0].connect_calls == 1
    assert connection.client is clients[0]
    assert connection.level_node is clients[0].nodes["level"]
    assert connection.enable_node is clients[0].nodes["enable"]
    assert connection.dac_node is clients[0].nodes["dac"]
    assert connection.raw_level == 14000.0
    assert connection.enable is True
    assert connection.dac == 2500


def test_open_br_connection_cleans_up_failed_client() -> None:
    client = create_fake_client(
        connect_error=ConnectionError("offline"),
    )

    with pytest.raises(ConnectionError, match="offline"):
        asyncio.run(
            open_br_connection(
                endpoint=client.endpoint,
                level_node_id="level",
                enable_node_id="enable",
                dac_node_id="dac",
                client_factory=lambda _: client,
            )
        )

    assert client.connect_calls == 1
    assert client.disconnect_calls == 1


def test_close_br_connection_ignores_cleanup_failure() -> None:
    client = create_fake_client(
        disconnect_error=ConnectionError("already closed"),
    )
    connection = BrConnection(
        client=client,
        level_node=client.nodes["level"],
        enable_node=client.nodes["enable"],
        dac_node=client.nodes["dac"],
        raw_level=14000.0,
        enable=True,
        dac=2500,
    )

    asyncio.run(close_br_connection(connection))

    assert client.disconnect_calls == 1


def test_synchronize_after_reconnection_discards_offline_commands() -> None:
    client = create_fake_client()
    connection = BrConnection(
        client=client,
        level_node=client.nodes["level"],
        enable_node=client.nodes["enable"],
        dac_node=client.nodes["dac"],
        raw_level=16000.0,
        enable=False,
        dac=750,
    )

    level_variable = FakeGatewayVariable()
    enable_command_variable = FakeGatewayVariable()
    dac_command_variable = FakeGatewayVariable()
    enable_feedback_variable = FakeGatewayVariable()
    dac_feedback_variable = FakeGatewayVariable()

    result = asyncio.run(
        synchronize_after_reconnection(
            connection=connection,
            level_variable=level_variable,
            enable_command_variable=enable_command_variable,
            dac_command_variable=dac_command_variable,
            enable_feedback_variable=enable_feedback_variable,
            dac_feedback_variable=dac_feedback_variable,
        )
    )

    assert result == (16000.0, False, 750)

    assert_variant(
        level_variable.written_variants[0],
        expected_value=16000.0,
        expected_type=ua.VariantType.Double,
    )
    assert_variant(
        enable_command_variable.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        dac_command_variable.written_variants[0],
        expected_value=750,
        expected_type=ua.VariantType.Int16,
    )
    assert_variant(
        enable_feedback_variable.written_variants[0],
        expected_value=False,
        expected_type=ua.VariantType.Boolean,
    )
    assert_variant(
        dac_feedback_variable.written_variants[0],
        expected_value=750,
        expected_type=ua.VariantType.Int16,
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
