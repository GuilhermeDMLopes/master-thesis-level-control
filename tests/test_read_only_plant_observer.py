from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "observe_real_plant_read_only.py"
)


def run_script(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def load_module():
    specification = importlib.util.spec_from_file_location(
        "read_only_plant_observer",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module

    try:
        specification.loader.exec_module(module)
    finally:
        sys.modules.pop(specification.name, None)

    return module


def test_help_is_offline() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "--plan" in result.stdout
    assert "--observe" in result.stdout
    assert "--label" in result.stdout
    assert "--duration-s" in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_empty_plan_is_read_only() -> None:
    result = run_script("--plan")

    assert result.returncode == 0
    assert "NETWORK ACCESS: NO" in result.stdout
    assert "OPC UA WRITES: NO" in result.stdout
    assert "GATEWAY CONNECTION: NO" in result.stdout
    assert "Label: NOT SET" in result.stdout
    assert "Duration: NOT SET" in result.stdout
    assert "OBSERVATION_READY" in result.stdout


def test_observe_requires_label_before_connection() -> None:
    result = run_script(
        "--observe",
        "--duration-s",
        "10",
    )

    assert result.returncode == 2
    assert "--label is required with --observe" in result.stderr
    assert "OBSERVATION_READY" not in result.stdout


def test_observe_requires_duration_before_connection() -> None:
    result = run_script(
        "--observe",
        "--label",
        "initial-band",
    )

    assert result.returncode == 2
    assert "--duration-s is required with --observe" in result.stderr
    assert "OBSERVATION_READY" not in result.stdout


def test_duration_requires_five_samples() -> None:
    result = run_script(
        "--plan",
        "--duration-s",
        "0.4",
        "--sample-s",
        "0.1",
    )

    assert result.returncode == 2
    assert "at least five sampling periods" in result.stderr


def test_zero_output_state_contract() -> None:
    module = load_module()
    safe = {
        "Enable": False,
        "DAC": 0,
        "AppliedEnable": False,
        "AppliedDAC": 0,
    }

    assert module.zero_output_state(safe) is True

    for field, value in (
        ("Enable", True),
        ("DAC", 1),
        ("AppliedEnable", True),
        ("AppliedDAC", 1),
    ):
        unsafe = dict(safe)
        unsafe[field] = value
        assert module.zero_output_state(unsafe) is False


def test_summary_reports_raw_noise() -> None:
    module = load_module()
    result = module.summarize_levels(
        [100, 101, 99, 100, 100]
    )

    assert result["minimum"] == 99.0
    assert result["maximum"] == 101.0
    assert result["median"] == 100.0
    assert result["mean"] == pytest.approx(100.0)
    assert result["peak_to_peak"] == 2.0


def test_source_contains_no_write_operation() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "write_attribute" not in source
    assert "write_value" not in source
    assert "gateway_endpoint" not in source


def test_import_has_no_execution_side_effects() -> None:
    module = load_module()

    assert callable(module.main)
    assert callable(module.run_observation)
    assert module.CONFIRMATION_TOKEN == "OBSERVATION_READY"
