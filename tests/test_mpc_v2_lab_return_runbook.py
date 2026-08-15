from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "experiments" / "mpc-v2-protected-lab-return-runbook-v1.md"
SMOKE = ROOT / "docs" / "experiments" / "mpc-v2-runtime-smoke-validation.md"
PREFLIGHT = ROOT / "scripts" / "mpc_v2_lab_return_preflight.ps1"


def test_v2_lab_return_artifacts_exist():
    assert RUNBOOK.is_file()
    assert SMOKE.is_file()
    assert PREFLIGHT.is_file()


def test_smoke_document_records_offline_acceptance():
    text = SMOKE.read_text(encoding="utf-8")
    assert "MPC_MOVE_BLOCKED_NMPC_V2 runtime type accepted: YES" in text
    assert "MPC_MEDIAN_FILTER_9 runtime type accepted: YES" in text
    assert "SAFE_DAC_RATE_LIMITER runtime type accepted: YES" in text
    assert "MpcInitMerge.EI1 triggered: NO" in text
    assert "REAL MPC FULL OPERATION AUTHORIZED: NO" in text


def test_runbook_keeps_v2_disabled_during_protected_deploy():
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "MpcController.ENABLE_REQUEST = FALSE" in text
    assert "MpcInitMerge.EI1" in text
    assert "exactly once" in text
    assert "WatchdogHealthy=True" in text
    assert "AppliedDAC=0" in text
    assert "REAL MPC FULL OPERATION AUTHORIZED: NO" in text


def test_preflight_is_read_only_and_pins_runtime_hash():
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173" in text
    assert "PLC ACCESS BY THIS SCRIPT: NO" in text
    assert "GATEWAY ACCESS BY THIS SCRIPT: NO" in text
    assert "FORTE START BY THIS SCRIPT: NO" in text
    assert "OPC UA WRITES BY THIS SCRIPT: NO" in text
    assert "Start-Process" not in text
    assert "asyncua" not in text.lower()
