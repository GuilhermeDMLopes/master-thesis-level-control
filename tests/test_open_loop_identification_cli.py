from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "scripts"
    / "open_loop_identification.py"
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


def test_help_is_offline_and_successful() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "--plan" in result.stdout
    assert "--execute" in result.stdout
    assert "--maximum-level-raw" in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_plan_is_offline_and_reports_defaults() -> None:
    result = run_script("--plan")

    assert result.returncode == 0
    assert "NETWORK ACCESS: NO" in result.stdout
    assert "ACTUATOR WRITES: NO" in result.stdout
    assert "Target DAC: 12000" in result.stdout
    assert (
        "NOT SET (required for --execute)"
        in result.stdout
    )
    assert "IDENTIFICATION_READY" in result.stdout


def test_mode_is_mandatory() -> None:
    result = run_script()

    assert result.returncode == 2
    assert (
        "one of the arguments --plan --execute is required"
        in result.stderr
    )
    assert "ConnectionRefusedError" not in result.stderr


def test_execute_requires_maximum_level_before_prompt() -> None:
    result = run_script("--execute")

    assert result.returncode == 2
    assert (
        "--maximum-level-raw is required with --execute"
        in result.stderr
    )
    assert "physical stop" not in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_invalid_target_dac_is_rejected_offline() -> None:
    result = run_script(
        "--plan",
        "--target-dac",
        "40000",
    )

    assert result.returncode == 2
    assert (
        "Target DAC must be between 0 and 32000"
        in result.stderr
    )
    assert "ConnectionRefusedError" not in result.stderr


def test_import_has_no_execution_side_effects() -> None:
    specification = importlib.util.spec_from_file_location(
        "open_loop_identification_under_test",
        SCRIPT_PATH,
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(
        specification
    )
    sys.modules[specification.name] = module

    try:
        specification.loader.exec_module(module)
    finally:
        sys.modules.pop(specification.name, None)

    assert callable(module.main)
    assert callable(module.run_experiment)
    assert (
        module.CONFIRMATION_TOKEN
        == "IDENTIFICATION_READY"
    )
