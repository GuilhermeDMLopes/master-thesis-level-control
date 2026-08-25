from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "plant" / "real-plant-plc-reference-v1.md"
EVIDENCE = ROOT / "docs" / "evidence" / "automation-studio-watchdog-v2"


def text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_reference_and_evidence_exist():
    assert DOC.is_file()
    assert EVIDENCE.is_dir()
    assert (EVIDENCE / "MANIFEST.sha256").is_file()


def test_plant_geometry_is_recorded_as_approximate():
    source = text()
    assert "approximately 28 cm" in source
    assert "approximately 1.5 cm" in source
    assert "approximately 1.3 cm" in source
    assert "approximately 40 cm" in source
    assert "25 cm" in source


def test_permanent_drain_behavior_is_explicit():
    source = text()
    assert "permanently open bottom drain" in source
    assert "water returns to the lower reservoir" in source


def test_plc_and_runtime_versions_are_recorded():
    source = text()
    assert "X20CP0483" in source
    assert "4.10.2.37" in source
    assert "B4.91" in source


def test_watchdog_task_basis_is_recorded():
    source = text()
    assert "100 ms" in source
    assert "WdTimeoutCycles := 10;" in source
    assert "10 cycles × 100 ms" in source


def test_watchdog_safe_output_gate_is_recorded():
    source = text()
    assert "EnableOut := AppliedEnable;" in source
    assert "DACOut := AppliedDAC;" in source
    assert "::Program:EnableOut" in source
    assert "::Program:DACOut" in source


def test_all_opcua_public_variables_are_recorded():
    source = text()
    for name in (
        "Nivel",
        "DAC",
        "Enable",
        "Heartbeat",
        "SafetyReset",
        "WatchdogHealthy",
        "WatchdogTripped",
        "AppliedEnable",
        "AppliedDAC",
    ):
        assert name in source


def test_current_br_nodeids_are_recorded():
    source = text()
    for name in (
        "Nivel",
        "Enable",
        "DAC",
        "Heartbeat",
        "SafetyReset",
        "WatchdogHealthy",
        "WatchdogTripped",
        "AppliedEnable",
        "AppliedDAC",
    ):
        assert f"ns=6;s=::Program:{name}" in source


def test_ton_failure_and_tonless_fix_are_documented():
    source = text()
    assert "Unknown data type: TON" in source
    assert "Build: 4 error(s), 7 warning(s)" in source
    assert "Errors displayed: 0" in source
    assert "Warnings displayed: 1" in source


def test_inverter_raw_parameters_are_preserved():
    source = text()
    for value in (
        "1103: 1",
        "1104: 0.0",
        "1105: 50.0",
        "1301: 0.0",
        "1302: 100.0",
        "2007: 0.0",
        "2008: 50.0",
        "2202: 5.0",
        "2203: 5.0",
        "9902: 1",
    ):
        assert value in source


def test_historical_pi_baseline_is_distinguished():
    source = text()
    assert "SP = 14.0 cm" in source
    assert "KP = 4.0" in source
    assert "KI = 0.50" in source
    assert "PV filter ALPHA = 0.95" in source


def test_current_nonlinear_model_reference_is_recorded():
    source = text()
    assert "tau_s = 32.0" in source
    assert "dead-zone DAC = 11750.0" in source
    assert "input exponent = 1.2" in source
    assert "10 / 10 scenarios" in source


def test_document_never_authorizes_real_mpc():
    source = text()
    assert "REAL MPC AUTHORIZED: **NO**" in source
    assert "MpcController.ENABLE_REQUEST = FALSE" in source


def test_original_evidence_archives_are_preserved():
    archives = EVIDENCE / "archives"
    assert archives.is_dir()
    assert len(list(archives.glob("*.zip"))) == 7


def test_exact_patch_script_is_extracted():
    matches = list(
        (EVIDENCE / "extracted").rglob(
            "apply_tonless_watchdog_patch.ps1"
        )
    )
    assert len(matches) == 1