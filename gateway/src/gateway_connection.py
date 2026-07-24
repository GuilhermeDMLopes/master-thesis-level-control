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
    raw_level: Any
    enable: Any
    dac: Any


async def open_br_connection(
    *,
    endpoint: str,
    level_node_id: str,
    enable_node_id: str,
    dac_node_id: str,
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

        raw_level = await level_node.read_value()
        enable = await enable_node.read_value()
        dac = await dac_node.read_value()

    except Exception:
        await close_br_client(client)
        raise

    return BrConnection(
        client=client,
        level_node=level_node,
        enable_node=enable_node,
        dac_node=dac_node,
        raw_level=raw_level,
        enable=enable,
        dac=dac,
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
