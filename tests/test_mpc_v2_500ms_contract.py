from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_mpc_v2_500ms.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_mpc_v2_500ms_under_test",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_preserves_physical_move_envelope():
    module = load_module()

    v1 = module.v1_config()
    v2 = module.v2_config()

    assert v1.sample_time_s == 0.1
    assert v1.maximum_delta_dac == 150.0

    assert v2.sample_time_s == 0.5
    assert v2.maximum_delta_dac == 750.0

    assert (
        v1.maximum_delta_dac / v1.sample_time_s
        == v2.maximum_delta_dac / v2.sample_time_s
        == 1500.0
    )


def test_v2_preserves_twenty_second_prediction_horizon():
    module = load_module()
    v2 = module.v2_config()

    assert v2.prediction_horizon_s == 20.0
    assert round(v2.prediction_horizon_s / v2.sample_time_s) == 40


def test_v2_reduces_prediction_grid_by_factor_five():
    module = load_module()

    v1 = module.v1_config()
    v2 = module.v2_config()

    v1_steps = round(v1.prediction_horizon_s / v1.sample_time_s)
    v2_steps = round(v2.prediction_horizon_s / v2.sample_time_s)

    assert v1_steps == 200
    assert v2_steps == 40
    assert v1_steps / v2_steps == 5


def test_gateway_boundary_model_remains_150_per_write():
    module = load_module()

    assert module.gateway_limit(0.0, 750.0) == 150.0
    assert module.gateway_limit(150.0, 750.0) == 300.0
    assert module.gateway_limit(750.0, 0.0) == 600.0


def test_nominal_v2_simulation_reaches_deadzone_safely():
    module = load_module()

    model = module.ref.load_model(module.MODEL_PATH)

    result = module.simulate(
        controller_model=model,
        physical_model=model,
        config=module.v2_config(),
    )

    assert not result["tripped"]
    assert result["max_applied_dac"] <= 12000.0
    assert result["max_raw"] < 650.0
    assert result["first_deadzone_s"] is not None
    assert result["first_deadzone_s"] <= 12.0
    assert 400.0 <= result["final_raw"] <= 500.0

def test_v2_analysis_registers_dynamic_reference_module():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "import sys" in source
    assert "sys.modules[spec.name] = module" in source

    registration = source.index(
        "sys.modules[spec.name] = module"
    )
    execution = source.index(
        "spec.loader.exec_module(module)"
    )

    assert registration < execution
