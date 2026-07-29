from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest
from asyncua import ua

from gateway_connection import BrConnection
from gateway_watchdog import (
    WatchdogStartupError,
    initialize_plc_watchdog,
    next_heartbeat_value,
    watchdog_permits_commands,
    write_safe_plc_commands,
)


@dataclass
class FakePlc:
    values: dict[str, Any] = field(
        default_factory=lambda: {
            "level": 237,
            "enable": True,
            "dac": 12000,
            "heartbeat": 0,
            "safety_reset": False,
            "watchdog_healthy": False,
            "watchdog_tripped": True,
            "applied_enable": False,
            "applied_dac": 0,
        }
    )
    writes: list[tuple[str, Any]] = field(
        default_factory=list
    )
    heartbeat_changes: int = 0
    arm_on_reset: bool = True

    def write(self, name: str, value: Any) -> None:
        previous = self.values[name]
        self.values[name] = value
        self.writes.append((name, value))

        if (
            name == "heartbeat"
            and value != previous
        ):
            self.heartbeat_changes += 1

        if (
            name == "safety_reset"
            and value is True
            and self.arm_on_reset
            and self.heartbeat_changes >= 2
            and self.values["enable"] is False
            and self.values["dac"] == 0
        ):
            self.values["watchdog_healthy"] = True
            self.values["watchdog_tripped"] = False


@dataclass
class FakeNode:
    plc: FakePlc
    name: str

    async def read_value(self) -> Any:
        return self.plc.values[self.name]

    async def write_attribute(
        self,
        attribute_id: Any,
        data_value: ua.DataValue,
    ) -> None:
        assert attribute_id == ua.AttributeIds.Value
        self.plc.write(
            self.name,
            data_value.Value.Value,
        )


def build_connection(plc: FakePlc) -> BrConnection:
    nodes = {
        name: FakeNode(plc, name)
        for name in plc.values
    }

    return BrConnection(
        client=None,
        level_node=nodes["level"],
        enable_node=nodes["enable"],
        dac_node=nodes["dac"],
        heartbeat_node=nodes["heartbeat"],
        safety_reset_node=nodes["safety_reset"],
        watchdog_healthy_node=nodes["watchdog_healthy"],
        watchdog_tripped_node=nodes["watchdog_tripped"],
        applied_enable_node=nodes["applied_enable"],
        applied_dac_node=nodes["applied_dac"],
        raw_level=plc.values["level"],
        enable=plc.values["enable"],
        dac=plc.values["dac"],
        heartbeat=plc.values["heartbeat"],
        safety_reset=plc.values["safety_reset"],
        watchdog_healthy=plc.values["watchdog_healthy"],
        watchdog_tripped=plc.values["watchdog_tripped"],
        applied_enable=plc.values["applied_enable"],
        applied_dac=plc.values["applied_dac"],
    )


@pytest.mark.parametrize(
    "current, expected",
    [
        (0, 1),
        (10, 11),
        (0xFFFFFFFE, 0xFFFFFFFF),
        (0xFFFFFFFF, 0),
    ],
)
def test_next_heartbeat_value_wraps_udint(
    current: int,
    expected: int,
) -> None:
    assert next_heartbeat_value(current) == expected


@pytest.mark.parametrize(
    "healthy, tripped, expected",
    [
        (True, False, True),
        (True, True, False),
        (False, False, False),
        (False, True, False),
    ],
)
def test_watchdog_permits_commands(
    healthy: bool,
    tripped: bool,
    expected: bool,
) -> None:
    assert watchdog_permits_commands(
        healthy=healthy,
        tripped=tripped,
    ) is expected


def test_write_safe_commands_disables_before_clearing_dac() -> None:
    plc = FakePlc()
    connection = build_connection(plc)

    asyncio.run(
        write_safe_plc_commands(connection)
    )

    assert plc.writes[:3] == [
        ("enable", False),
        ("dac", 0),
        ("safety_reset", False),
    ]


def test_initialize_watchdog_forces_safe_state_and_arms() -> None:
    plc = FakePlc()
    connection = build_connection(plc)

    result = asyncio.run(
        initialize_plc_watchdog(
            connection=connection,
            heartbeat_period_s=0.001,
            reset_pulse_s=0.001,
            startup_timeout_s=0.05,
            poll_period_s=0.001,
        )
    )

    assert result.state.enable is False
    assert result.state.dac == 0
    assert result.state.watchdog_healthy is True
    assert result.state.watchdog_tripped is False
    assert result.state.applied_enable is False
    assert result.state.applied_dac == 0
    assert plc.heartbeat_changes >= 2
    assert plc.values["safety_reset"] is False


def test_initialize_watchdog_rejects_nonzero_applied_output() -> None:
    plc = FakePlc()
    plc.values["applied_dac"] = 12000
    connection = build_connection(plc)

    with pytest.raises(
        WatchdogStartupError,
        match="applied outputs",
    ):
        asyncio.run(
            initialize_plc_watchdog(
                connection=connection,
                heartbeat_period_s=0.001,
                reset_pulse_s=0.001,
                startup_timeout_s=0.05,
                poll_period_s=0.001,
            )
        )

    assert plc.values["enable"] is False
    assert plc.values["dac"] == 0
    assert plc.values["safety_reset"] is False


def test_initialize_watchdog_times_out_fail_closed() -> None:
    plc = FakePlc(arm_on_reset=False)
    connection = build_connection(plc)

    with pytest.raises(
        WatchdogStartupError,
        match="startup timeout",
    ):
        asyncio.run(
            initialize_plc_watchdog(
                connection=connection,
                heartbeat_period_s=0.001,
                reset_pulse_s=0.001,
                startup_timeout_s=0.01,
                poll_period_s=0.001,
            )
        )

    assert plc.values["enable"] is False
    assert plc.values["dac"] == 0
    assert plc.values["safety_reset"] is False


@pytest.mark.parametrize(
    "parameter_name",
    [
        "heartbeat_period_s",
        "reset_pulse_s",
        "startup_timeout_s",
        "poll_period_s",
    ],
)
def test_initialize_watchdog_rejects_nonpositive_timing(
    parameter_name: str,
) -> None:
    plc = FakePlc()
    arguments = {
        "connection": build_connection(plc),
        "heartbeat_period_s": 0.001,
        "reset_pulse_s": 0.001,
        "startup_timeout_s": 0.01,
        "poll_period_s": 0.001,
    }
    arguments[parameter_name] = 0.0

    with pytest.raises(
        ValueError,
        match=f"{parameter_name} must be greater than zero",
    ):
        asyncio.run(
            initialize_plc_watchdog(**arguments)
        )
