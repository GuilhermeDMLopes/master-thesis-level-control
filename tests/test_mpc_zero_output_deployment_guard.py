from __future__ import annotations

import ast
import asyncio
import importlib.util
import math
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = ROOT / "scripts" / "mpc_zero_output_deployment_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location(
        "mpc_zero_output_deployment_guard_under_test",
        GUARD_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard():
    return load_guard()


def zero_snapshot() -> dict[str, object]:
    return {
        "gw_nivel": 298.0,
        "gw_enable": False,
        "gw_dac": 0.0,
        "gw_applied_enable": False,
        "gw_applied_dac": 0.0,
        "gw_watchdog_healthy": True,
        "plc_enable": False,
        "plc_dac": 0.0,
        "plc_applied_enable": False,
        "plc_applied_dac": 0.0,
        "plc_watchdog_healthy": True,
    }


def test_guard_file_exists():
    assert GUARD_PATH.is_file()


def test_default_endpoints_are_the_established_project_contract(guard):
    assert guard.DEFAULT_GATEWAY_ENDPOINT == "opc.tcp://127.0.0.1:4841"
    assert guard.DEFAULT_GATEWAY_URI == "urn:br-4diac-gateway"
    assert guard.DEFAULT_PLC_ENDPOINT == "opc.tcp://10.0.0.3:4840"


def test_exact_br_plc_nodeids_are_pinned(guard):
    expected = {
        "Nivel": "ns=6;s=::Program:Nivel",
        "Enable": "ns=6;s=::Program:Enable",
        "DAC": "ns=6;s=::Program:DAC",
        "Heartbeat": "ns=6;s=::Program:Heartbeat",
        "SafetyReset": "ns=6;s=::Program:SafetyReset",
        "WatchdogHealthy": "ns=6;s=::Program:WatchdogHealthy",
        "WatchdogTripped": "ns=6;s=::Program:WatchdogTripped",
        "AppliedEnable": "ns=6;s=::Program:AppliedEnable",
        "AppliedDAC": "ns=6;s=::Program:AppliedDAC",
    }

    assert guard.PLC_IDS == expected


def test_obsolete_asglobalpv_nodeids_are_not_present():
    source = GUARD_PATH.read_text(encoding="utf-8")
    assert "::AsGlobalPV:Program:" not in source


def test_guard_python_ast_contains_no_opcua_write_calls():
    source = GUARD_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_exact = {
        "write_value",
        "write_attribute",
        "write_values",
        "set_value",
        "set_values",
    }

    observed: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        name = None

        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id

        if name in forbidden_exact:
            observed.append(name)

    assert observed == []


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, True),
        (0.0, True),
        (1e-10, True),
        (-1e-10, True),
        (1e-6, False),
        (-1.0, False),
    ],
)
def test_exact_zero_contract(guard, value, expected):
    assert guard.exact_zero(value) is expected


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_finite_number_rejects_non_finite_values(guard, value):
    with pytest.raises(RuntimeError, match="non-finite"):
        guard.finite_number(value)


@pytest.mark.parametrize(
    "value, expected",
    [
        (False, False),
        (True, True),
        (0, False),
        (1, True),
    ],
)
def test_bool_value_accepts_only_bool_compatible_values(guard, value, expected):
    assert guard.bool_value(value) is expected


@pytest.mark.parametrize("value", [-1, 2, 0.5, "TRUE", None])
def test_bool_value_rejects_invalid_values(guard, value):
    with pytest.raises(RuntimeError, match="unexpected BOOL-compatible"):
        guard.bool_value(value)


def test_assert_zero_output_accepts_complete_zero_state(guard):
    guard.assert_zero_output(zero_snapshot())


@pytest.mark.parametrize(
    "field, bad_value, expected_fragment",
    [
        ("gw_enable", True, "gateway Enable"),
        ("gw_dac", 1.0, "gateway DAC"),
        ("gw_applied_enable", True, "gateway AppliedEnable"),
        ("gw_applied_dac", -1.0, "gateway AppliedDAC"),
        ("plc_enable", True, "PLC Enable"),
        ("plc_dac", 1.0, "PLC DAC"),
        ("plc_applied_enable", True, "PLC AppliedEnable"),
        ("plc_applied_dac", 1.0, "PLC AppliedDAC"),
    ],
)
def test_each_nonzero_actuator_state_trips_guard(
    guard,
    field,
    bad_value,
    expected_fragment,
):
    snapshot = zero_snapshot()
    snapshot[field] = bad_value

    with pytest.raises(RuntimeError) as excinfo:
        guard.assert_zero_output(snapshot)

    message = str(excinfo.value)
    assert "ZERO-OUTPUT VIOLATION" in message
    assert expected_fragment in message


def test_multiple_simultaneous_violations_are_reported(guard):
    snapshot = zero_snapshot()
    snapshot["gw_enable"] = True
    snapshot["gw_dac"] = 100.0
    snapshot["plc_applied_dac"] = 50.0

    with pytest.raises(RuntimeError) as excinfo:
        guard.assert_zero_output(snapshot)

    message = str(excinfo.value)

    assert "gateway Enable" in message
    assert "gateway DAC" in message
    assert "PLC AppliedDAC" in message


def test_plc_resolver_reads_only_exact_required_br_nodes(guard):
    class FakeNode:
        def __init__(self, identifier: str):
            self.identifier = identifier
            self.read_count = 0

        async def read_value(self):
            self.read_count += 1

            if self.identifier.endswith(":Enable"):
                return False
            if self.identifier.endswith(":AppliedEnable"):
                return False
            if self.identifier.endswith(":WatchdogHealthy"):
                return True
            return 0

    class FakeClient:
        def __init__(self):
            self.requested: list[str] = []
            self.nodes: dict[str, FakeNode] = {}

        def get_node(self, identifier: str):
            self.requested.append(identifier)
            node = self.nodes.get(identifier)

            if node is None:
                node = FakeNode(identifier)
                self.nodes[identifier] = node

            return node

    client = FakeClient()
    resolved = asyncio.run(guard.resolve_plc_nodes(client))

    expected_ids = [
        guard.PLC_IDS["Enable"],
        guard.PLC_IDS["DAC"],
        guard.PLC_IDS["AppliedEnable"],
        guard.PLC_IDS["AppliedDAC"],
        guard.PLC_IDS["WatchdogHealthy"],
    ]

    assert client.requested == expected_ids

    assert resolved.enable.identifier == guard.PLC_IDS["Enable"]
    assert resolved.dac.identifier == guard.PLC_IDS["DAC"]
    assert resolved.applied_enable.identifier == guard.PLC_IDS["AppliedEnable"]
    assert resolved.applied_dac.identifier == guard.PLC_IDS["AppliedDAC"]
    assert (
        resolved.watchdog_healthy.identifier
        == guard.PLC_IDS["WatchdogHealthy"]
    )

    for identifier in expected_ids:
        assert client.nodes[identifier].read_count == 1


def run_plan(*extra_args: str) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(GUARD_PATH),
        "--plan",
        *extra_args,
    ]

    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_plan_mode_is_offline_and_read_only():
    result = run_plan(
        "--duration-s",
        "10",
        "--sample-s",
        "0.1",
    )

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "MPC ZERO-OUTPUT DEPLOYMENT GUARD PLAN" in output
    assert "NETWORK ACCESS: NO" in output
    assert "OPC UA WRITES: NO" in output
    assert "FORTE DEPLOYMENT AUTOMATION: NO" in output
    assert "ACTUATOR COMMANDS: NO" in output
    assert "MPC_ZERO_OUTPUT_GUARD_READY" in output


def test_plan_documents_short_preflight_and_protected_deployment():
    result = run_plan()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "short preflight" in output
    assert "ResRealRawMPCV1" in output
    assert "ENABLE_REQUEST" in output
    assert "MpcInitMerge.EI1" in output


@pytest.mark.parametrize(
    "args, message",
    [
        (("--duration-s", "0"), "duration must be positive"),
        (("--duration-s", "-1"), "duration must be positive"),
        (("--sample-s", "0"), "sample period must be positive"),
        (("--sample-s", "-0.1"), "sample period must be positive"),
    ],
)
def test_invalid_timing_is_rejected_before_observation(args, message):
    result = run_plan(*args)

    assert result.returncode != 0
    assert message in (result.stdout + result.stderr)


def test_plan_and_observe_are_mutually_exclusive():
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD_PATH),
            "--plan",
            "--observe",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "not allowed with argument" in result.stderr


def test_mode_is_mandatory():
    result = subprocess.run(
        [sys.executable, str(GUARD_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "one of the arguments --plan --observe is required" in result.stderr


def test_plan_does_not_create_raw_data_directory(tmp_path):
    output_root = tmp_path / "must-not-be-created"

    result = run_plan(
        "--output-root",
        str(output_root),
    )

    assert result.returncode == 0, result.stderr
    assert not output_root.exists()