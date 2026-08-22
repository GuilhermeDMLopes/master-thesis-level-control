from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "local_deadzone_resume_11650_11900.py"
WRAPPER = ROOT / "scripts" / "run_local_deadzone_resume_11650_11900.ps1"


def runner_text() -> str:
    return RUNNER.read_text(encoding="utf-8-sig")


def wrapper_text() -> str:
    return WRAPPER.read_text(encoding="utf-8-sig")


def test_runner_python_syntax():
    ast.parse(runner_text())


def test_exact_remaining_points():
    text = runner_text()
    assert "REMAINING_DAC_POINTS = (11650, 11700, 11750, 11800, 11850, 11900)" in text
    assert "11600" not in text.split("REMAINING_DAC_POINTS =", 1)[1].splitlines()[0]


def test_target_acquisition_gate_contract():
    text = runner_text()
    assert "TARGET_TOLERANCE_DAC = 5.0" in text
    assert "TARGET_CONFIRM_SAMPLES = 5" in text
    assert "TARGET_ACQUISITION_TIMEOUT_S = 30.0" in text
    assert "Starting full {CONSTANT_TARGET_HOLD_S:.1f} s constant-target hold NOW." in text


def test_constant_target_hold_is_45_seconds():
    assert "CONSTANT_TARGET_HOLD_S = 45.0" in runner_text()


def test_rebaseline_contract():
    text = runner_text()
    assert "MINIMUM_ZERO_RECOVERY_S = 30.0" in text
    assert "STABLE_REBASELINE_WINDOW_S = 20.0" in text
    assert "STABLE_MAX_ABS_SLOPE_RAW_PER_S = 1.0" in text
    assert "STABLE_MAX_MEDIAN9_RANGE_RAW = 30.0" in text
    assert "MAXIMUM_PHYSICAL_HEIGHT_BEFORE_NEXT_POINT_CM = 1.0" in text


def test_safety_contract_unchanged():
    text = runner_text()
    assert "MAX_INSTANT_RAW = 1100.0" in text
    assert "MAX_MEDIAN9_RAW = 1100.0" in text
    assert "MAX_POSITIVE_MEDIAN_RATE_RAW_PER_S = 180.0" in text
    assert "MAX_DAC = 12000.0" in text
    assert "ACTIVE_PHYSICAL_ABORT_CM = 5.0" in text


def test_delta_median_logged():
    text = runner_text()
    assert '"delta_median9_raw"' in text
    assert "median9 - local_baseline" in text


def test_plan_mode_does_not_import_asyncua_at_module_top_level():
    tree = ast.parse(runner_text())
    top_level_imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            top_level_imports.append(node.module or "")
    assert not any(name.startswith("asyncua") for name in top_level_imports)


def test_plan_mode_runs_offline():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--plan"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "NETWORK ACCESS: NO" in result.stdout
    assert "REAL ACTUATION: NO" in result.stdout
    assert "11600 automatic repetition:       NO" in result.stdout


def test_wrapper_blocks_forte_and_requires_physical_confirmation():
    text = wrapper_text()
    assert "Get-Process forte" in text
    assert "LOCAL_DEADZONE_RESUME_PHYSICAL_READY" in text
    assert "DO NOT RUN THIS WRAPPER WITHOUT PHYSICAL ACCESS TO THE PLANT." in text


def test_wrapper_runs_python_file_not_python_stdin():
    text = wrapper_text()
    assert "& $Python $Runner --run --evidence-dir $EvidenceDir" in text
    assert "| & $Python -" not in text
