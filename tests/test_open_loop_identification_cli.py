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


def load_module():
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

    return module


def test_help_is_offline_and_successful() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "--plan" in result.stdout
    assert "--execute" in result.stdout
    assert "--dac-step" in result.stdout
    assert "--initial-level-min-raw" in result.stdout
    assert "--initial-level-max-raw" in result.stdout
    assert "--maximum-level-raw" in result.stdout
    assert "--target-dac" not in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_plan_has_no_excitation_defaults() -> None:
    result = run_script("--plan")

    assert result.returncode == 0
    assert "NETWORK ACCESS: NO" in result.stdout
    assert "ACTUATOR WRITES: NO" in result.stdout
    assert "DAC sequence: NOT SET" in result.stdout
    assert "Initial raw-level minimum: NOT SET" in result.stdout
    assert "Maximum raw-level trip: NOT SET" in result.stdout
    assert "IDENTIFICATION_READY" in result.stdout
    assert "12000" not in result.stdout


def test_plan_reports_repeated_dac_steps() -> None:
    result = run_script(
        "--plan",
        "--dac-step",
        "8000:5",
        "--dac-step",
        "9000:7.5",
    )

    assert result.returncode == 0
    assert "step 1: DAC=8000, hold=5.000 s" in result.stdout
    assert "step 2: DAC=9000, hold=7.500 s" in result.stdout
    assert "Total positive-DAC hold time: 12.500 s" in result.stdout


def test_mode_is_mandatory() -> None:
    result = run_script()

    assert result.returncode == 2
    assert (
        "one of the arguments --plan --execute is required"
        in result.stderr
    )
    assert "ConnectionRefusedError" not in result.stderr


def test_execute_requires_dac_steps_before_prompt() -> None:
    result = run_script("--execute")

    assert result.returncode == 2
    assert (
        "At least one --dac-step is required with --execute"
        in result.stderr
    )
    assert "physical stop" not in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_execute_requires_maximum_level_before_prompt() -> None:
    result = run_script(
        "--execute",
        "--dac-step",
        "8000:5",
    )

    assert result.returncode == 2
    assert (
        "--maximum-level-raw is required with --execute"
        in result.stderr
    )
    assert "physical stop" not in result.stdout
    assert "ConnectionRefusedError" not in result.stderr


def test_execute_requires_initial_minimum_before_prompt() -> None:
    result = run_script(
        "--execute",
        "--dac-step",
        "8000:5",
        "--maximum-level-raw",
        "1000",
    )

    assert result.returncode == 2
    assert (
        "--initial-level-min-raw is required with --execute"
        in result.stderr
    )
    assert "physical stop" not in result.stdout


def test_execute_requires_initial_maximum_before_prompt() -> None:
    result = run_script(
        "--execute",
        "--dac-step",
        "8000:5",
        "--maximum-level-raw",
        "1000",
        "--initial-level-min-raw",
        "100",
    )

    assert result.returncode == 2
    assert (
        "--initial-level-max-raw is required with --execute"
        in result.stderr
    )
    assert "physical stop" not in result.stdout


def test_invalid_step_dac_is_rejected_offline() -> None:
    result = run_script(
        "--plan",
        "--dac-step",
        "40000:5",
    )

    assert result.returncode == 2
    assert (
        "Step DAC must be between 1 and 32000"
        in result.stderr
    )
    assert "ConnectionRefusedError" not in result.stderr


def test_invalid_step_format_is_rejected_offline() -> None:
    result = run_script(
        "--plan",
        "--dac-step",
        "8000",
    )

    assert result.returncode == 2
    assert (
        "DAC step must use DAC:HOLD_S format"
        in result.stderr
    )


def test_initial_band_must_be_ordered() -> None:
    result = run_script(
        "--plan",
        "--initial-level-min-raw",
        "500",
        "--initial-level-max-raw",
        "400",
    )

    assert result.returncode == 2
    assert (
        "Initial raw-level minimum must be lower"
        in result.stderr
    )


def test_initial_maximum_must_be_below_trip() -> None:
    result = run_script(
        "--plan",
        "--initial-level-min-raw",
        "100",
        "--initial-level-max-raw",
        "1000",
        "--maximum-level-raw",
        "1000",
    )

    assert result.returncode == 2
    assert (
        "Initial raw-level maximum must be lower than "
        "the maximum raw-level trip threshold"
        in result.stderr
    )


def test_parser_builds_ordered_steps() -> None:
    module = load_module()
    parser = module.build_parser()
    args = parser.parse_args(
        [
            "--plan",
            "--dac-step",
            "7000:4",
            "--dac-step",
            "8500:6",
        ]
    )
    config = module.config_from_args(args)

    assert [step.dac for step in config.steps] == [
        7000,
        8500,
    ]
    assert [step.hold_s for step in config.steps] == [
        4.0,
        6.0,
    ]


def test_import_has_no_execution_side_effects() -> None:
    module = load_module()

    assert callable(module.main)
    assert callable(module.run_experiment)
    assert callable(module.parse_dac_step)
    assert module.CONFIRMATION_TOKEN == "IDENTIFICATION_READY"
