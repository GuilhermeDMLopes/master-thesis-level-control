from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from asyncua import ua

from gateway_connection import (
    BrConnection,
    BrRuntimeState,
    read_br_runtime_state,
)


class WatchdogStartupError(RuntimeError):
    """Raised when the PLC watchdog cannot be armed safely."""


@dataclass(frozen=True)
class WatchdogStartupResult:
    """Safe PLC state confirmed after a watchdog handshake."""

    heartbeat_value: int
    state: BrRuntimeState


async def write_value_only(
    node: Any,
    value: Any,
    variant_type: ua.VariantType,
) -> None:
    """
    Write only the Value attribute of an OPC UA node.

    B&R rejects writes that include status or timestamps for these variables.
    """
    await node.write_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(
                value,
                variant_type,
            )
        ),
    )


def next_heartbeat_value(current_value: Any) -> int:
    """Increment a PLC UDINT heartbeat with deterministic wraparound."""
    return (int(current_value) + 1) & 0xFFFFFFFF


def watchdog_permits_commands(
    *,
    healthy: Any,
    tripped: Any,
) -> bool:
    """Return whether external Enable and DAC commands may reach the PLC."""
    return bool(healthy) and not bool(tripped)


async def write_safe_plc_commands(
    connection: BrConnection,
) -> None:
    """
    Force the PLC command interface to its safe state.

    Enable is removed before DAC is cleared so the physical gate closes first.
    """
    await write_value_only(
        connection.enable_node,
        False,
        ua.VariantType.Boolean,
    )
    await write_value_only(
        connection.dac_node,
        0,
        ua.VariantType.Int16,
    )
    await write_value_only(
        connection.safety_reset_node,
        False,
        ua.VariantType.Boolean,
    )


async def write_next_heartbeat(
    connection: BrConnection,
    current_value: Any,
) -> int:
    """Write and return the next UDINT heartbeat value."""
    next_value = next_heartbeat_value(current_value)

    await write_value_only(
        connection.heartbeat_node,
        next_value,
        ua.VariantType.UInt32,
    )

    return next_value


async def initialize_plc_watchdog(
    *,
    connection: BrConnection,
    heartbeat_period_s: float,
    reset_pulse_s: float,
    startup_timeout_s: float,
    poll_period_s: float,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> WatchdogStartupResult:
    """
    Arm the PLC watchdog only after forcing all commands to zero.

    The sequence is intentionally fail-closed:

    1. Write Enable=False, DAC=0, and SafetyReset=False.
    2. Produce two observable Heartbeat changes.
    3. Apply one SafetyReset rising-edge pulse.
    4. Continue Heartbeat updates while waiting for the PLC.
    5. Accept the handshake only when the watchdog is healthy and both
       applied outputs remain zero.
    """
    timing_values = {
        "heartbeat_period_s": heartbeat_period_s,
        "reset_pulse_s": reset_pulse_s,
        "startup_timeout_s": startup_timeout_s,
        "poll_period_s": poll_period_s,
    }

    for name, value in timing_values.items():
        if float(value) <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero"
            )

    heartbeat_value = int(
        await connection.heartbeat_node.read_value()
    ) & 0xFFFFFFFF

    try:
        await write_safe_plc_commands(connection)

        heartbeat_value = await write_next_heartbeat(
            connection,
            heartbeat_value,
        )
        await sleep(heartbeat_period_s)

        heartbeat_value = await write_next_heartbeat(
            connection,
            heartbeat_value,
        )
        await sleep(heartbeat_period_s)

        # Guarantee a low state before the rising edge.
        await write_value_only(
            connection.safety_reset_node,
            False,
            ua.VariantType.Boolean,
        )
        await sleep(poll_period_s)

        await write_value_only(
            connection.safety_reset_node,
            True,
            ua.VariantType.Boolean,
        )
        await sleep(reset_pulse_s)

        await write_value_only(
            connection.safety_reset_node,
            False,
            ua.VariantType.Boolean,
        )

        deadline = monotonic() + startup_timeout_s
        last_heartbeat_write = monotonic()

        while True:
            now = monotonic()

            if (
                now - last_heartbeat_write
                >= heartbeat_period_s
            ):
                heartbeat_value = await write_next_heartbeat(
                    connection,
                    heartbeat_value,
                )
                last_heartbeat_write = now

            state = await read_br_runtime_state(connection)

            if (
                state.applied_enable
                or state.applied_dac != 0
            ):
                raise WatchdogStartupError(
                    "PLC applied outputs were nonzero during "
                    "the watchdog handshake"
                )

            if watchdog_permits_commands(
                healthy=state.watchdog_healthy,
                tripped=state.watchdog_tripped,
            ):
                if state.enable or state.dac != 0:
                    raise WatchdogStartupError(
                        "PLC command variables were not safe after "
                        "the watchdog handshake"
                    )

                return WatchdogStartupResult(
                    heartbeat_value=heartbeat_value,
                    state=state,
                )

            if now >= deadline:
                raise WatchdogStartupError(
                    "PLC watchdog did not become healthy before "
                    "the startup timeout"
                )

            await sleep(poll_period_s)

    except Exception:
        try:
            await write_safe_plc_commands(connection)
        except Exception:
            pass

        raise
