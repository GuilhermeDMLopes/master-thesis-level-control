from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from asyncua import Client


@dataclass(frozen=True)
class BrConnection:
    """Active OPC UA connection and node references for the B&R PLC."""

    client: Any
    level_node: Any
    enable_node: Any
    dac_node: Any
    heartbeat_node: Any
    safety_reset_node: Any
    watchdog_healthy_node: Any
    watchdog_tripped_node: Any
    applied_enable_node: Any
    applied_dac_node: Any
    raw_level: Any
    enable: Any
    dac: Any
    heartbeat: Any
    safety_reset: Any
    watchdog_healthy: Any
    watchdog_tripped: Any
    applied_enable: Any
    applied_dac: Any


@dataclass(frozen=True)
class BrRuntimeState:
    """One coherent set of values read from the connected PLC."""

    raw_level: float
    enable: bool
    dac: int
    heartbeat: int
    safety_reset: bool
    watchdog_healthy: bool
    watchdog_tripped: bool
    applied_enable: bool
    applied_dac: int


async def read_br_runtime_state(
    connection: BrConnection,
) -> BrRuntimeState:
    """Read command, process, and watchdog values from the PLC."""
    return BrRuntimeState(
        raw_level=float(
            await connection.level_node.read_value()
        ),
        enable=bool(
            await connection.enable_node.read_value()
        ),
        dac=int(
            await connection.dac_node.read_value()
        ),
        heartbeat=int(
            await connection.heartbeat_node.read_value()
        ),
        safety_reset=bool(
            await connection.safety_reset_node.read_value()
        ),
        watchdog_healthy=bool(
            await connection.watchdog_healthy_node.read_value()
        ),
        watchdog_tripped=bool(
            await connection.watchdog_tripped_node.read_value()
        ),
        applied_enable=bool(
            await connection.applied_enable_node.read_value()
        ),
        applied_dac=int(
            await connection.applied_dac_node.read_value()
        ),
    )


async def open_br_connection(
    *,
    endpoint: str,
    level_node_id: str,
    enable_node_id: str,
    dac_node_id: str,
    heartbeat_node_id: str,
    safety_reset_node_id: str,
    watchdog_healthy_node_id: str,
    watchdog_tripped_node_id: str,
    applied_enable_node_id: str,
    applied_dac_node_id: str,
    client_factory: Callable[[str], Any] = Client,
) -> BrConnection:
    """
    Create a fresh OPC UA client, connect it, and read the initial PLC state.

    A new Client instance is created for every attempt. This is required after
    asyncua closes a session because a stopped PLC or simulator cannot be
    recovered by continuing to use the old Client instance.
    """
    client = client_factory(endpoint)

    try:
        await client.connect()

        level_node = client.get_node(level_node_id)
        enable_node = client.get_node(enable_node_id)
        dac_node = client.get_node(dac_node_id)
        heartbeat_node = client.get_node(heartbeat_node_id)
        safety_reset_node = client.get_node(safety_reset_node_id)
        watchdog_healthy_node = client.get_node(
            watchdog_healthy_node_id
        )
        watchdog_tripped_node = client.get_node(
            watchdog_tripped_node_id
        )
        applied_enable_node = client.get_node(
            applied_enable_node_id
        )
        applied_dac_node = client.get_node(
            applied_dac_node_id
        )

        raw_level = await level_node.read_value()
        enable = await enable_node.read_value()
        dac = await dac_node.read_value()
        heartbeat = await heartbeat_node.read_value()
        safety_reset = await safety_reset_node.read_value()
        watchdog_healthy = (
            await watchdog_healthy_node.read_value()
        )
        watchdog_tripped = (
            await watchdog_tripped_node.read_value()
        )
        applied_enable = (
            await applied_enable_node.read_value()
        )
        applied_dac = await applied_dac_node.read_value()

    except Exception:
        await close_br_client(client)
        raise

    return BrConnection(
        client=client,
        level_node=level_node,
        enable_node=enable_node,
        dac_node=dac_node,
        heartbeat_node=heartbeat_node,
        safety_reset_node=safety_reset_node,
        watchdog_healthy_node=watchdog_healthy_node,
        watchdog_tripped_node=watchdog_tripped_node,
        applied_enable_node=applied_enable_node,
        applied_dac_node=applied_dac_node,
        raw_level=raw_level,
        enable=enable,
        dac=dac,
        heartbeat=heartbeat,
        safety_reset=safety_reset,
        watchdog_healthy=watchdog_healthy,
        watchdog_tripped=watchdog_tripped,
        applied_enable=applied_enable,
        applied_dac=applied_dac,
    )


async def close_br_client(client: Any | None) -> None:
    """Disconnect an OPC UA client without hiding the original failure."""
    if client is None:
        return

    try:
        await asyncio.wait_for(
            client.disconnect(),
            timeout=2.0,
        )
    except (Exception, asyncio.TimeoutError):
        # A client whose transport is already closed commonly raises during
        # disconnect. Reconnection must not be blocked by cleanup failure.
        return


async def close_br_connection(
    connection: BrConnection | None,
) -> None:
    """Close an active B&R connection when one exists."""
    if connection is None:
        return

    await close_br_client(connection.client)
