from __future__ import annotations

import importlib.util
import math
import sys
from collections import deque
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mpc_reference_controller_v3.py"
MODEL = ROOT / "models" / "mpc" / "delayed-hammerstein-v3-candidate.json"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "mpc_reference_controller_v3_under_test",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def module():
    return load_module()


@pytest.fixture()
def model(module):
    return module.load_v3_model(MODEL)


def warm_zero_history(controller, model):
    for _ in range(model.transport_delay_steps):
        output = controller.step(
            measured_raw=model.baseline_raw,
            applied_dac=0.0,
            enable_request=False,
            external_healthy=True,
        )
        assert output.command_enable is False
        assert output.command_dac == 0.0


def test_v3_model_constants_match_identified_candidate(model):
    assert model.baseline_raw == pytest.approx(288.0)
    assert model.transport_delay_steps == 18
    assert model.transport_delay_s == pytest.approx(9.0)
    assert model.tau_s == pytest.approx(4.75)
    assert model.sample_time_s == pytest.approx(0.5)
    assert model.discrete_a == pytest.approx(
        0.900087626252259,
        abs=5e-13,
    )
    assert model.discrete_b == pytest.approx(
        0.067989118863552,
        abs=5e-13,
    )


def test_v3_has_exact_30s_60_step_750_dac_contract(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    assert controller._prediction_steps == 60
    assert controller.config.maximum_delta_dac == 750.0
    assert controller.config.maximum_dac == 12000.0
    assert len(controller.target_candidates) == 13


def test_bias_adaptation_is_disabled(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    warm_zero_history(controller, model)

    output = controller.step(
        measured_raw=350.0,
        applied_dac=0.0,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is False
    assert output.input_bias_estimate_dac == 0.0

    source = SCRIPT.read_text(encoding="utf-8")
    assert "_update_bias_estimate" not in source
    assert "bias_adaptation_gain" not in source


def test_enable_before_18_history_samples_fails_closed(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)

    for _ in range(17):
        controller.step(
            measured_raw=model.baseline_raw,
            applied_dac=0.0,
            enable_request=False,
            external_healthy=True,
        )

    output = controller.step(
        measured_raw=model.baseline_raw,
        applied_dac=0.0,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is True
    assert output.trip_reason == "DELAY_HISTORY_NOT_READY"
    assert output.command_enable is False
    assert output.command_dac == 0.0


def test_disabled_cycles_fill_history_without_actuation(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)

    warm_zero_history(controller, model)

    assert controller.delay_history_ready is True
    assert controller.delay_history_samples == 18

    output = controller.step(
        measured_raw=model.baseline_raw,
        applied_dac=0.0,
        enable_request=False,
        external_healthy=True,
    )

    assert output.command_enable is False
    assert output.command_dac == 0.0
    assert output.tripped is False
    assert output.delay_history_ready is True


def test_reset_does_not_erase_committed_applied_history(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)

    for _ in range(model.transport_delay_steps):
        controller.step(
            measured_raw=350.0,
            applied_dac=12000.0,
            enable_request=False,
            external_healthy=True,
        )

    before = tuple(controller._delay_history)
    assert set(before) == {12000.0}

    controller.reset()

    after = tuple(controller._delay_history)
    assert after == before
    assert controller.delay_history_ready is True


def test_candidate_prediction_uses_committed_history_before_new_command(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    warm_zero_history(controller, model)

    history = tuple(controller._delay_history)

    # New candidate commands cannot affect the model during the first
    # 18 x 500 ms of an all-zero committed pipeline.
    y = model.baseline_raw
    queue = deque(history, maxlen=model.transport_delay_steps)
    command = 0.0
    first_nonzero_effect_step = None

    for prediction_step in range(1, 50):
        command = module._rate_limit(
            command,
            12000.0,
            750.0,
            0.0,
            12000.0,
        )
        delayed = queue.popleft()
        queue.append(command)
        y_next = module.delayed_plant_step(y, delayed, model)

        if abs(y_next - model.baseline_raw) > 1e-9:
            first_nonzero_effect_step = prediction_step
            break

        y = y_next

    assert first_nonzero_effect_step is not None
    assert first_nonzero_effect_step > model.transport_delay_steps


def test_full_committed_12000_pipeline_causes_preemptive_command_reduction(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)

    for _ in range(model.transport_delay_steps):
        controller.step(
            measured_raw=350.0,
            applied_dac=12000.0,
            enable_request=False,
            external_healthy=True,
        )

    output = controller.step(
        measured_raw=350.0,
        applied_dac=12000.0,
        enable_request=True,
        external_healthy=True,
    )

    assert output.tripped is False
    assert output.command_enable is True
    assert output.command_dac < 12000.0
    assert output.predicted_max_raw > 650.0
    assert output.predicted_max_raw < 750.0


def test_move_limit_and_envelope_hold(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    warm_zero_history(controller, model)

    applied = 0.0

    for _ in range(20):
        output = controller.step(
            measured_raw=model.baseline_raw,
            applied_dac=applied,
            enable_request=True,
            external_healthy=True,
        )

        assert output.tripped is False
        assert 0.0 <= output.command_dac <= 12000.0
        assert abs(output.command_dac - applied) <= 750.0 + 1e-9
        applied = output.command_dac


def test_ideal_delayed_closed_loop_reaches_target_without_overshoot(module, model):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    warm_zero_history(controller, model)

    plant_queue = deque(
        [0.0] * model.transport_delay_steps,
        maxlen=model.transport_delay_steps,
    )

    y = model.baseline_raw
    applied = 0.0
    levels = []

    for _ in range(180):
        output = controller.step(
            measured_raw=y,
            applied_dac=applied,
            enable_request=True,
            external_healthy=True,
        )

        assert output.tripped is False
        assert output.command_enable is True

        delayed_u = plant_queue.popleft()
        plant_queue.append(applied)

        y = module.delayed_plant_step(
            y,
            delayed_u,
            model,
        )
        applied = output.command_dac
        levels.append(y)

    assert max(levels) <= 500.0
    assert levels[-1] == pytest.approx(450.0, abs=3.0)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"external_healthy": False}, "EXTERNAL_HEALTH_FALSE"),
        ({"measured_raw": 800.0}, "MEASURED_LEVEL_HARD_LIMIT"),
        ({"applied_dac": 12001.0}, "APPLIED_DAC_OUTSIDE_STAGE_ENVELOPE"),
        ({"setpoint_raw": 800.0}, "SETPOINT_OUTSIDE_SAFE_RANGE"),
    ],
)
def test_fail_closed_conditions(module, model, kwargs, reason):
    controller = module.SafeDelayedMoveBlockedNMPCV3(model)
    warm_zero_history(controller, model)

    args = {
        "measured_raw": 350.0,
        "applied_dac": 0.0,
        "enable_request": True,
        "external_healthy": True,
    }
    args.update(kwargs)

    output = controller.step(**args)

    assert output.tripped is True
    assert output.trip_reason == reason
    assert output.command_enable is False
    assert output.command_dac == 0.0


def test_reference_implementation_is_offline_only():
    source = SCRIPT.read_text(encoding="utf-8").lower()

    for forbidden in (
        "asyncua",
        "opc.tcp://",
        "write_attribute(",
        "write_value(",
        "subprocess",
        "socket",
    ):
        assert forbidden not in source
