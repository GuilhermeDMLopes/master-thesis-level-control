from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MPC = ROOT / "data/sample/mpc-v4-target17000-20260829"
PI = ROOT / "data/sample/pi-v4-matched-20260901"
PI_FIRST = ROOT / "data/sample/pi-v4-matched-first-attempt-20260829"
COMPARISON = ROOT / "data/sample/pi-vs-mpc-v4-final-20260901"
FIGURES = ROOT / "docs/figures/pi-vs-mpc-v4-final-20260901"


EXPECTED_HASHES = {
    PI / "first-active-monitor.csv":
        "376264ABED7960451E0F62ECD4DEC5BD13E49EDC42ADBB9483D84AB158B019E8",
    PI / "predeployment-zero-output-monitor.csv":
        "CCE68B1DEE1DB384D74BDEEE699D7B0AADA2FFF4E7D2EED37E88659A32054C05",
    PI / "postshutdown-zero-output-monitor.csv":
        "D3E98307DAA0FFB9E73034288F7B7040796C4670EFD0063528320259795D7766",
    PI / "gateway-full-session.csv":
        "3F9DDD7258AAC1B12F30A6E9A5D061D8F13D00BE264DEE6E32082C3B5E4B973F",
    PI / "physical-observation.txt":
        "A784EF3D26DC608830C9C2C788B4DE23C60D08792CB606612024684364E6971E",
    PI_FIRST / "first-active-monitor.csv":
        "84065A1DCC77F9C1B56A0BE75D92CD184C0A9AB3FE65048143BC8279EE7CEC00",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def metrics() -> dict[str, object]:
    return json.loads((COMPARISON / "metrics.json").read_text(encoding="utf-8"))


def test_exact_pi_evidence_bytes_are_preserved():
    for path, expected in EXPECTED_HASHES.items():
        assert path.is_file()
        assert sha256(path) == expected


def test_final_pi_run_contract_and_physical_result():
    data = metrics()["pi_final_ki_0_10"]
    assert 179.8 <= data["active_duration_s"] <= 180.1
    assert data["maximum_applied_dac"] == 16000.0
    assert data["maximum_median_raw"] == 16148.0
    assert data["physical_final_height_cm"] == 14.7
    assert data["overshoot_percent"] == 0.0
    assert data["watchdog_healthy_all_active"] is True


def test_final_mpc_reference_remains_authoritative():
    data = metrics()["mpc_v4"]
    assert 179.8 <= data["active_duration_s"] <= 180.1
    assert data["maximum_median_raw"] == 17086.0
    assert data["physical_final_height_cm"] == 15.0
    assert 0.50 <= data["overshoot_percent"] <= 0.51
    assert data["watchdog_healthy_all_active"] is True


def test_both_final_runs_have_independent_safe_zero_evidence():
    data = metrics()
    for key in ("mpc_v4", "pi_final_ki_0_10"):
        assert data[key]["predeployment_zero"]["all_zero_and_healthy"] is True
        assert data[key]["postshutdown_zero"]["all_zero_and_healthy"] is True
    assert data["mpc_v4"]["postshutdown_zero"]["samples"] == 74
    assert data["pi_final_ki_0_10"]["postshutdown_zero"]["samples"] == 80


def test_first_pi_attempt_is_preserved_as_retuning_evidence():
    data = metrics()["pi_first_attempt_ki_0_02"]
    assert data["physical_final_height_cm"] == 6.0
    assert data["maximum_median_raw"] == 6257.0
    assert data["first_90_percent_s"] is None
    assert data["watchdog_healthy_all_active"] is True


def test_comparison_metrics_are_consistent_and_bounded():
    data = metrics()
    relative = data["relative_comparison"]
    assert data["status"] == "final_real_plant_comparison_complete"
    assert 3.08 <= relative["pi_minus_mpc_iae_percent"] <= 3.10
    assert -5.47 <= relative["pi_minus_mpc_ise_percent"] <= -5.45
    assert 7.47 <= relative["pi_to_mpc_tail30_mean_error_ratio"] <= 7.48
    assert 16.93 <= relative["pi_minus_mpc_total_variation_percent"] <= 16.94


def test_reproducible_document_and_figures_exist():
    document = ROOT / "docs/experiments/pi-vs-mpc-v4-final-20260901-analysis.md"
    text = document.read_text(encoding="utf-8")
    assert "Final PI versus MPC V4 real-plant comparison" in text
    assert "14.7 cm" in text
    assert "statistical superiority claim" in text
    for name in (
        "pi-mpc-v4-level-comparison.png",
        "pi-mpc-v4-level-comparison.svg",
        "pi-mpc-v4-dac-comparison.png",
        "pi-mpc-v4-dac-comparison.svg",
    ):
        assert (FIGURES / name).is_file()


def test_analysis_is_offline_only_and_uses_preserved_inputs():
    script = (ROOT / "scripts/analyze_pi_mpc_v4_final.py").read_text(
        encoding="utf-8"
    )
    assert "asyncua" not in script
    assert "socket" not in script
    assert "subprocess" not in script
    assert "first-active-monitor.csv" in script
    assert "postshutdown-zero-output-monitor.csv" in script
    assert "TARGET_RAW = 17000.0" in script
