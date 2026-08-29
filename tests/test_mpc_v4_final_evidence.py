from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "sample" / "mpc-v4-target17000-20260829"
ACTIVE = EVIDENCE / "first-active-monitor.csv"
PRE = EVIDENCE / "predeployment-zero-output-monitor.csv"
POST = EVIDENCE / "postshutdown-zero-output-monitor.csv"
METRICS = EVIDENCE / "metrics.json"
PHYSICAL = EVIDENCE / "physical-observation.txt"
GATEWAY = EVIDENCE / "gateway-full-session.csv"
FORTE_LOG = EVIDENCE / "forte-v4.err.log"
MODEL = ROOT / "models" / "mpc" / "high-range-hammerstein-v4-candidate.json"
ANALYSIS = ROOT / "scripts" / "analyze_mpc_v4_target17000.py"
REPORT = ROOT / "docs" / "experiments" / "mpc-v4-target17000-20260829-analysis.md"
FIGURES = ROOT / "docs" / "figures" / "mpc-v4-target17000"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def test_final_v4_evidence_files_exist():
    for path in (
        ACTIVE,
        PRE,
        POST,
        METRICS,
        PHYSICAL,
        GATEWAY,
        FORTE_LOG,
        MODEL,
        ANALYSIS,
        REPORT,
    ):
        assert path.is_file(), path
    for name in (
        "mpc-v4-target17000-level.png",
        "mpc-v4-target17000-level.svg",
        "mpc-v4-target17000-dac.png",
        "mpc-v4-target17000-dac.svg",
        "mpc-v4-target17000-error.png",
        "mpc-v4-target17000-error.svg",
    ):
        assert (FIGURES / name).is_file(), name


def test_final_v4_raw_evidence_hashes_are_frozen():
    assert sha256(ACTIVE) == "B2315428080F2BEA7C2FC294CF5EE8CB95311C4134A5D2F1C9AD17E1D6A99854"
    assert sha256(PRE) == "2D962725335492212FD6D2DA41F92862A58DF397DEE9176DEE1A5F5E27B883C0"
    assert sha256(POST) == "21680C23F3412DC40040C2D6ACF349A77AA1612F1BF4B3BF9F080392BA7AE23A"
    assert sha256(PHYSICAL) == "5644F53A4331D7A9E0163B7ADD275701EBEC0A3569F9C6DBD82C7EBA93BB508C"
    assert sha256(GATEWAY) == "C5925D875FF48EE8F93DB90B1AA4DCF20711EB17D0906934E459F630E5113EE7"
    assert sha256(FORTE_LOG) == "84FC1CD9CE400E13E71FA22BAE3852748DB81B9B8F23DC4DA17D1010767964C8"


def test_final_v4_completed_full_active_window():
    samples = [row for row in rows(ACTIVE) if float(row["active_elapsed_s"]) >= 0.0]
    assert len(samples) == 1481
    assert 179.9 <= float(samples[-1]["active_elapsed_s"]) <= 180.1
    assert max(float(row["plc_applied_dac"]) for row in samples) == 16000.0


def test_final_v4_tracking_metrics_match_preserved_csv():
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    assert metrics["target_raw"] == 17000.0
    assert metrics["physical_height_cm"] == 15.0
    assert metrics["shutdown_reason"] == "ACTIVE_WINDOW_COMPLETE"
    assert abs(metrics["maximum_median_raw"] - 17086.0) < 1e-9
    assert abs(metrics["overshoot_percent"] - 0.5058823529411764) < 1e-12
    assert abs(metrics["tail30_mean_raw"] - 16848.453441295547) < 1e-9
    assert abs(metrics["tail30_mean_applied_dac"] - 14092.914979757084) < 1e-9


def test_final_v4_watchdog_remained_healthy_during_active_run():
    samples = [row for row in rows(ACTIVE) if float(row["active_elapsed_s"]) >= 0.0]
    assert all(row["gw_watchdog_healthy"] == "True" for row in samples)
    assert all(row["plc_watchdog_healthy"] == "True" for row in samples)
    assert all(row["plc_watchdog_tripped"] == "False" for row in samples)


def test_final_v4_predeployment_and_postshutdown_are_zero():
    for path, expected_count in ((PRE, 695), (POST, 74)):
        samples = rows(path)
        assert len(samples) == expected_count
        assert all(row["gw_enable"] == "False" for row in samples)
        assert all(float(row["gw_dac"]) == 0.0 for row in samples)
        assert all(row["plc_applied_enable"] == "False" for row in samples)
        assert all(float(row["plc_applied_dac"]) == 0.0 for row in samples)


def test_final_v4_model_records_completed_bounded_validation():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    assert model["status"] == "validated_real_high_range_15cm"
    final = model["final_v4_real_observation"]
    assert final["physical_height_cm"] == 15.0
    assert final["active_duration_s"] == 179.969
    assert final["watchdog_healthy_all_active"] is True
    assert final["postshutdown_zero_verified"] is True
    assert model["authorization"]["future_real_actuation_authorized"] is False


def test_final_v4_analysis_is_offline_and_documentation_has_no_mojibake():
    source = ANALYSIS.read_text(encoding="utf-8").lower()
    for forbidden in (
        "from asyncua",
        "import asyncua",
        "opc.tcp://",
        "write_value(",
        "start-process",
    ):
        assert forbidden not in source
    for path in (REPORT, ROOT / "docs" / "experiments" / "mpc-v4-high-range-validation.md"):
        text = path.read_text(encoding="utf-8")
        mojibake_tokens = tuple(chr(codepoint) for codepoint in (0x00E2, 0x00C3, 0x00C2, 0xFFFD))
        assert not any(token in text for token in mojibake_tokens)

    for svg_path in sorted(FIGURES.glob("*.svg")):
        lines = svg_path.read_text(encoding="utf-8").splitlines()
        assert all(line == line.rstrip() for line in lines), svg_path
