from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MODEL = (
    ROOT
    / "models"
    / "mpc"
    / "delayed-hammerstein-v3-candidate.json"
)

CANONICAL = (
    ROOT
    / "models"
    / "mpc"
    / "deadzone-hammerstein-v1.json"
)

ACTIVE = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3-real-evidence"
    / "first-active-v2-20260818-192023.csv"
)

EMPTY = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3-real-evidence"
    / "empty-baseline-20260818-192945.csv"
)

ANALYSIS = ROOT / "scripts" / "identify_delayed_hammerstein_v3.py"
REPORT = ROOT / "docs" / "mpc" / "delayed-hammerstein-v3-identification.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_evidence_and_outputs_exist():
    for path in (
        MODEL,
        CANONICAL,
        ACTIVE,
        EMPTY,
        ANALYSIS,
        REPORT,
    ):
        assert path.is_file(), path


def test_preserved_evidence_hashes_match_model_manifest():
    model = load(MODEL)
    evidence = model["evidence"]

    assert (
        evidence["active_commissioning"]["sha256"]
        == sha256(ACTIVE)
    )
    assert (
        evidence["empty_baseline"]["sha256"]
        == sha256(EMPTY)
    )
    assert (
        evidence["static_model_source"]["sha256"]
        == sha256(CANONICAL)
    )


def test_empty_baseline_is_physical_zero_reference():
    model = load(MODEL)
    physical = model["physical_context"]
    empty = model["empty_baseline_observation"]

    assert physical["empty_tank_height_cm"] == 0.0
    assert 270.0 <= physical["empty_tank_raw_offset"] <= 305.0
    assert physical["central_bottom_drain"] is True

    assert empty["minimum_raw"] >= 250.0
    assert empty["maximum_raw"] <= 320.0
    assert abs(empty["final_raw"] - empty["initial_raw"]) <= 30.0


def test_static_nonlinearity_is_preserved_from_canonical_model():
    v3 = load(MODEL)
    canonical = load(CANONICAL)["continuous_time"]
    static = v3["static_nonlinearity"]

    assert static["deadzone_DAC"] == float(
        canonical["deadzone_DAC"]
    )
    assert static["input_exponent_p"] == float(
        canonical["input_exponent_p"]
    )
    assert static[
        "equilibrium_gain_G_raw_per_DAC_power_p"
    ] == float(
        canonical[
            "equilibrium_gain_G_raw_per_DAC_power_p"
        ]
    )


def test_v3_dynamic_fit_is_delay_aware_and_materially_better():
    fit = load(MODEL)["dynamic_fit_500ms"]

    assert 12 <= fit["transport_delay_steps"] <= 24
    assert (
        fit["transport_delay_s"]
        == 0.5 * fit["transport_delay_steps"]
    )
    assert 1.0 <= fit["tau_s"] <= 12.0
    assert fit["rmse_raw"] <= 25.0
    assert fit["rmse_ratio_v3_over_v2"] <= 0.40
    assert fit["canonical_v2_replay_rmse_raw"] > fit["rmse_raw"]
    assert 7.0 <= fit["empirical_effective_delay_s"] <= 13.0


def test_v3_controller_contract_keeps_actuator_envelope_but_extends_horizon():
    contract = load(MODEL)["controller_contract_proposal"]

    assert contract["sample_time_s"] == 0.5
    assert contract["prediction_horizon_s"] == 30.0
    assert contract["prediction_steps"] == 60
    assert contract["target_candidates"] == 13
    assert contract["candidate_prediction_iterations"] == 780

    assert contract["maximum_delta_dac_per_update"] == 750.0
    assert contract["minimum_dac"] == 0.0
    assert contract["maximum_dac"] == 12000.0

    assert (
        contract["prediction_requires_applied_dac_history_queue"]
        is True
    )
    assert contract["history_queue_length_samples"] >= 12


def test_target_equilibrium_remains_near_previous_commissioning_region():
    target = load(MODEL)["target_implication"]

    assert target["target_raw"] == 450.0
    assert 11750.0 <= target["implied_equilibrium_DAC"] <= 12000.0


def test_analysis_is_offline_only():
    source = ANALYSIS.read_text(encoding="utf-8").lower()

    for forbidden in (
        "from asyncua",
        "import asyncua",
        "opc.tcp://",
        "write_attribute(",
        "write_value(",
        "set_writable(",
    ):
        assert forbidden not in source


def test_active_evidence_contains_real_12000_dac_region():
    with ACTIVE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    applied = [
        float(row["gw_applied_dac"])
        for row in rows
        if row.get("gw_applied_dac", "").strip()
    ]

    assert applied
    assert max(applied) == 12000.0


def test_authorization_remains_false():
    model = load(MODEL)

    assert (
        model["authorization"]["real_mpc_full_operation_authorized"]
        is False
    )
    assert (
        model["authorization"]["real_actuation_performed_by_this_analysis"]
        is False
    )
