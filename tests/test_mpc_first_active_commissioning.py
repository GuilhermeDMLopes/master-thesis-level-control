from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mpc_first_active_commissioning.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "mpc_first_active_commissioning_under_test",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def module():
    return load_module()


def safe_snapshot():
    return {
        "gw_nivel": 288.0,
        "gw_enable": False,
        "gw_dac": 0.0,
        "gw_applied_enable": False,
        "gw_applied_dac": 0.0,
        "gw_watchdog_healthy": True,
        "plc_nivel": 288.0,
        "plc_enable": False,
        "plc_dac": 0.0,
        "plc_applied_enable": False,
        "plc_applied_dac": 0.0,
        "plc_watchdog_healthy": True,
        "plc_watchdog_tripped": False,
    }


def test_script_exists():
    assert SCRIPT.is_file()


def test_exact_plc_nodeids_are_used(module):
    assert module.PLC_IDS["Nivel"] == "ns=6;s=::Program:Nivel"
    assert module.PLC_IDS["Enable"] == "ns=6;s=::Program:Enable"
    assert module.PLC_IDS["DAC"] == "ns=6;s=::Program:DAC"
    assert (
        module.PLC_IDS["WatchdogHealthy"]
        == "ns=6;s=::Program:WatchdogHealthy"
    )
    assert (
        module.PLC_IDS["WatchdogTripped"]
        == "ns=6;s=::Program:WatchdogTripped"
    )


def test_initial_safe_state_passes(module):
    module.assert_initial_safe(
        safe_snapshot(),
        240.0,
        340.0,
    )


@pytest.mark.parametrize(
    "field, value",
    [
        ("gw_enable", True),
        ("gw_dac", 1.0),
        ("gw_applied_enable", True),
        ("gw_applied_dac", 1.0),
        ("plc_enable", True),
        ("plc_dac", 1.0),
        ("plc_applied_enable", True),
        ("plc_applied_dac", 1.0),
        ("gw_watchdog_healthy", False),
        ("plc_watchdog_healthy", False),
        ("plc_watchdog_tripped", True),
    ],
)
def test_initial_unsafe_states_fail(module, field, value):
    state = safe_snapshot()
    state[field] = value

    with pytest.raises(RuntimeError):
        module.assert_initial_safe(
            state,
            240.0,
            340.0,
        )


@pytest.mark.parametrize("level", [239.0, 341.0])
def test_initial_level_band_is_enforced(module, level):
    state = safe_snapshot()
    state["gw_nivel"] = level

    with pytest.raises(RuntimeError):
        module.assert_initial_safe(
            state,
            240.0,
            340.0,
        )


def test_nominal_active_snapshot_passes(module):
    state = safe_snapshot()
    state.update(
        {
            "gw_enable": True,
            "gw_dac": 11800.0,
            "gw_applied_enable": True,
            "gw_applied_dac": 11800.0,
            "plc_enable": True,
            "plc_dac": 11800.0,
            "plc_applied_enable": True,
            "plc_applied_dac": 11800.0,
        }
    )

    module.assert_active_limits(
        state,
        420.0,
        80.0,
        maximum_median_raw=550.0,
        maximum_instant_raw=700.0,
        maximum_rate_raw_per_s=180.0,
        maximum_dac=12000.0,
    )


@pytest.mark.parametrize(
    "change, median_raw, rate",
    [
        ({"gw_watchdog_healthy": False}, 420.0, 80.0),
        ({"plc_watchdog_healthy": False}, 420.0, 80.0),
        ({"plc_watchdog_tripped": True}, 420.0, 80.0),
        ({"gw_dac": 12001.0}, 420.0, 80.0),
        ({"gw_applied_dac": 12001.0}, 420.0, 80.0),
        ({"plc_dac": 12001.0}, 420.0, 80.0),
        ({"plc_applied_dac": 12001.0}, 420.0, 80.0),
        ({"gw_nivel": 700.0}, 420.0, 80.0),
        ({}, 550.0, 80.0),
        ({}, 420.0, 180.0),
    ],
)
def test_active_safety_violations_fail(module, change, median_raw, rate):
    state = safe_snapshot()
    state.update(
        {
            "gw_enable": True,
            "gw_dac": 11800.0,
            "gw_applied_enable": True,
            "gw_applied_dac": 11800.0,
            "plc_enable": True,
            "plc_dac": 11800.0,
            "plc_applied_enable": True,
            "plc_applied_dac": 11800.0,
        }
    )
    state.update(change)

    with pytest.raises(RuntimeError):
        module.assert_active_limits(
            state,
            median_raw,
            rate,
            maximum_median_raw=550.0,
            maximum_instant_raw=700.0,
            maximum_rate_raw_per_s=180.0,
            maximum_dac=12000.0,
        )


def test_source_never_contains_positive_actuator_write():
    source = SCRIPT.read_text(encoding="utf-8")

    forbidden = (
        "write_value(True",
        "Variant(True",
        "write_value(1",
        "Variant(1,",
        "write_value(12000",
        "write_value(11750",
    )

    for token in forbidden:
        assert token not in source


def test_zero_output_writes_are_explicit(module):
    import inspect

    source = inspect.getsource(module.force_zero_outputs)

    assert "write_value_only(" in source
    assert "ua.VariantType.Boolean" in source
    assert "ua.VariantType.Int16" in source
    assert ".write_value(" not in source


def test_safety_reset_is_never_written():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))

    # SafetyReset may exist in the NodeId inventory, but there must be no
    # attribute access that writes through a safety-reset node.
    source = SCRIPT.read_text(encoding="utf-8")
    assert "safety_reset.write" not in source.lower()


def run_plan(*args: str):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--plan",
            *args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_plan_mode_is_non_actuating():
    result = run_plan()

    assert result.returncode == 0, result.stderr
    assert "THIS STAGE CAN PRODUCE REAL PUMP ACTUATION." in result.stdout
    assert "Supervisor positive actuator writes: NO" in result.stdout
    assert "Supervisor safe-zero writes on abort/end: YES" in result.stdout
    assert "FIRST_ACTIVE_MPC_READY" in result.stdout


def test_plan_pins_bounded_defaults():
    result = run_plan()
    assert result.returncode == 0, result.stderr

    output = result.stdout
    assert "Active window: 15.0 s" in output
    assert "Maximum DAC: 12000.0" in output
    assert "Maximum rolling-median raw: 550.0" in output
    assert "Maximum instantaneous raw: 700.0" in output
    assert "180.0 raw/s" in output


@pytest.mark.parametrize(
    "args, message",
    [
        (("--active-duration-s", "0"), "active duration must be positive"),
        (
            ("--active-duration-s", "21"),
            "first active duration must not exceed 20 s",
        ),
        (("--maximum-dac", "12001"), "maximum DAC must be in 1..12000"),
        (("--sample-s", "0"), "sample period must be positive"),
    ],
)
def test_invalid_safety_parameters_are_rejected(args, message):
    result = run_plan(*args)
    assert result.returncode != 0
    assert message in (result.stdout + result.stderr)


def test_run_requires_forte_pid():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--forte-pid is required" in (result.stdout + result.stderr)


def test_write_value_only_uses_value_attribute_without_timestamps(module):
    import asyncio

    class FakeNode:
        def __init__(self):
            self.calls = []

        async def write_attribute(self, attribute, data_value):
            self.calls.append((attribute, data_value))

    node = FakeNode()

    asyncio.run(
        module.write_value_only(
            node,
            0,
            module.ua.VariantType.Int16,
        )
    )

    assert len(node.calls) == 1

    attribute, data_value = node.calls[0]

    assert attribute == module.ua.AttributeIds.Value
    assert data_value.Value.Value == 0
    assert data_value.Value.VariantType == module.ua.VariantType.Int16


def test_safe_shutdown_source_uses_value_only_helper():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "async def write_value_only" in source

    force_zero = source.split(
        "async def force_zero_outputs",
        1,
    )[1].split(
        "async def verify_final_zero",
        1,
    )[0]

    assert ".write_value(" not in force_zero
    assert "write_value_only(" in force_zero


def test_verified_zero_is_not_reclassified_unsafe_only_for_write_warning():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "FINAL ZERO OUTPUT VERIFIED DESPITE WRITE WARNING: YES" in source
    assert (
        "zero output was verified, but one or more explicit zero writes "
        "reported an error"
    ) not in source
