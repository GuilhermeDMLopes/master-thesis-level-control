from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "mpc_reference_controller.py"
MODEL_PATH = (
    ROOT
    / "models"
    / "mpc"
    / "deadzone-hammerstein-v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "mpc_reference_controller",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def mpc():
    module = load_module()
    model = module.load_model(MODEL_PATH)
    return module, module.SafeMoveBlockedNMPC(model)


def test_model_contract_is_physical(mpc):
    module, controller = mpc
    model = controller.model

    assert model.tau_s > 0
    assert model.equilibrium_gain > 0
    assert model.exponent > 0
    assert model.deadzone_dac >= 0


def test_stage_envelope_is_frozen_at_12000():
    module = load_module()
    model = module.load_model(MODEL_PATH)

    with pytest.raises(ValueError):
        module.SafeMoveBlockedNMPC(
            model,
            module.MPCConfig(maximum_dac=12001.0),
        )


def test_disabled_is_zero_without_trip(mpc):
    _, controller = mpc

    output = controller.step(
        measured_raw=298.0,
        applied_dac=0.0,
        enable_request=False,
        external_healthy=True,
    )

    assert output.command_enable is False
    assert output.command_dac == 0.0
    assert output.tripped is False


def test_external_health_false_fails_closed_and_latches(mpc):
    _, controller = mpc

    output = controller.step(
        measured_raw=450.0,
        applied_dac=11800.0,
        enable_request=True,
        external_healthy=False,
    )

    assert output.command_enable is False
    assert output.command_dac == 0.0
    assert output.tripped is True
    assert output.trip_reason == "EXTERNAL_HEALTH_FALSE"

    second = controller.step(
        measured_raw=450.0,
        applied_dac=0.0,
        enable_request=True,
        external_healthy=True,
    )

    assert second.tripped is True
    assert second.command_dac == 0.0


def test_reset_clears_latched_trip(mpc):
    _, controller = mpc

    controller.step(
        measured_raw=float("nan"),
        applied_dac=0.0,
        enable_request=True,
        external_healthy=True,
    )

    output = controller.step(
        measured_raw=298.0,
        applied_dac=0.0,
        enable_request=False,
        external_healthy=True,
        reset_request=True,
    )

    assert output.tripped is False
    assert output.command_dac == 0.0


@pytest.mark.parametrize(
    "bad_pv",
    [float("nan"), float("inf"), float("-inf")],
)
def test_nonfinite_pv_fails_closed(mpc, bad_pv):
    _, controller = mpc

    output = controller.step(
        measured_raw=bad_pv,
        applied_dac=0.0,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is True
    assert output.command_enable is False
    assert output.command_dac == 0.0


def test_measured_hard_limit_fails_closed(mpc):
    _, controller = mpc

    output = controller.step(
        measured_raw=800.0,
        applied_dac=11800.0,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is True
    assert output.trip_reason == "MEASURED_LEVEL_HARD_LIMIT"
    assert output.command_dac == 0.0


@pytest.mark.parametrize("bad_dac", [-1.0, 12000.1])
def test_applied_dac_outside_stage_envelope_fails_closed(mpc, bad_dac):
    _, controller = mpc

    output = controller.step(
        measured_raw=450.0,
        applied_dac=bad_dac,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is True
    assert output.trip_reason == "APPLIED_DAC_OUTSIDE_STAGE_ENVELOPE"
    assert output.command_dac == 0.0


def test_active_output_respects_dac_and_move_constraints(mpc):
    _, controller = mpc

    applied = 0.0

    for _ in range(100):
        output = controller.step(
            measured_raw=298.0,
            applied_dac=applied,
            enable_request=True,
            external_healthy=True,
        )

        assert output.tripped is False
        assert 0.0 <= output.command_dac <= 12000.0
        assert abs(output.command_dac - applied) <= 150.0 + 1e-9
        assert output.command_enable is True

        applied = output.command_dac


def test_bias_estimate_is_bounded(mpc):
    module, controller = mpc

    applied = 11850.0

    for _ in range(1000):
        output = controller.step(
            measured_raw=700.0,
            applied_dac=applied,
            enable_request=True,
            external_healthy=True,
        )

        if output.tripped:
            break

        applied = output.command_dac

    assert (
        abs(controller.input_bias_estimate_dac)
        <= controller.config.maximum_abs_input_bias_dac
        + 1e-9
    )


def test_nominal_closed_loop_reaches_setpoint_without_hard_violation(mpc):
    module, controller = mpc

    y = controller.model.baseline_raw
    applied = 0.0
    values = []

    for _ in range(900):
        output = controller.step(
            measured_raw=y,
            applied_dac=applied,
            enable_request=True,
            external_healthy=True,
        )

        assert output.tripped is False
        assert output.command_enable is True
        assert 0.0 <= output.command_dac <= 12000.0
        assert abs(output.command_dac - applied) <= 150.0 + 1e-9

        applied = output.command_dac
        y = module.plant_step(
            y,
            applied,
            controller.model,
            controller.config.sample_time_s,
        )

        assert y < 800.0
        values.append(y)

    tail = values[-200:]
    mae = sum(abs(value - 450.0) for value in tail) / len(tail)

    assert mae < 15.0
    assert max(values) < 650.0


def test_controller_is_deterministic_for_identical_state(mpc):
    module, controller_a = mpc
    model = controller_a.model
    controller_b = module.SafeMoveBlockedNMPC(model)

    state = dict(
        measured_raw=400.0,
        applied_dac=11750.0,
        enable_request=True,
        external_healthy=True,
    )

    a = controller_a.step(**state)
    b = controller_b.step(**state)

    assert a == b


def test_negative_gain_model_is_rejected(tmp_path):
    module = load_module()
    document = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    document["continuous_time"][
        "equilibrium_gain_G_raw_per_DAC_power_p"
    ] = -1.0

    bad = tmp_path / "bad-model.json"
    bad.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError):
        module.load_model(bad)
