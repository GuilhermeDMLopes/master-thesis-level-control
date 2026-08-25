from pathlib import Path
import importlib.util
import math

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "mpc_reference_controller_v3h.py"

spec = importlib.util.spec_from_file_location("mpc_reference_controller_v3h_test", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)


def make():
    return m.SafeDelayedMoveBlockedNMPCV3H(
        m.load_default_model(),
        config=m.default_v3e_config(),
        disturbance_alpha=0.10,
    )


def test_v3h_alpha_contract():
    c = make()
    assert c.disturbance_alpha == 0.10
    assert c.disturbance_hat_raw_per_step == 0.0


def test_v3e_runtime_contract_preserved():
    c = make()
    assert c.config.sample_time_s == 0.5
    assert c.model.transport_delay_steps == 18
    assert c.config.prediction_horizon_s == 30.0
    assert c.config.maximum_delta_dac == 750.0
    assert c.config.minimum_dac == 0.0
    assert c.config.maximum_dac == 12000.0
    assert c.config.predicted_soft_level_raw == 1100.0
    assert c.config.predicted_hard_level_raw == 1400.0
    assert c.config.measured_hard_level_raw == 1500.0
    assert len(c.target_candidates) == 13


def test_canonical_targets_are_preserved_exactly():
    model = m.load_default_model()
    config = m.default_v3e_config()
    canonical = m.v3.SafeDelayedMoveBlockedNMPCV3(model, config=config)
    v3h = m.SafeDelayedMoveBlockedNMPCV3H(model, config=config)
    assert tuple(v3h.target_candidates) == tuple(canonical.target_candidates)


def test_positive_innovation_learns_positive_state_disturbance():
    c = make()
    pred = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_disturbance(
        measured_raw=pred + 100.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(
        c.disturbance_hat_raw_per_step,
        10.0,
        abs_tol=1e-9,
    )


def test_disturbance_ewma_is_causal():
    c = make()

    pred1 = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_disturbance(
        measured_raw=pred1 + 100.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(c.disturbance_hat_raw_per_step, 10.0, abs_tol=1e-9)

    pred2 = c.canonical_one_step_prediction(
        previous_measured_raw=510.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_disturbance(
        measured_raw=pred2 + 100.0,
        previous_measured_raw=510.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(c.disturbance_hat_raw_per_step, 19.0, abs_tol=1e-9)


def test_disturbance_is_bounded():
    c = m.SafeDelayedMoveBlockedNMPCV3H(
        m.load_default_model(),
        config=m.default_v3e_config(),
        disturbance_alpha=1.0,
        disturbance_limit_raw_per_step=50.0,
    )

    pred = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_disturbance(
        measured_raw=pred + 1000.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert c.disturbance_hat_raw_per_step == 50.0


def test_zero_disturbance_reproduces_canonical_candidate_cost():
    model = m.load_default_model()
    config = m.default_v3e_config()

    canonical = m.v3.SafeDelayedMoveBlockedNMPCV3(model, config=config)
    v3h = m.SafeDelayedMoveBlockedNMPCV3H(model, config=config)

    history = tuple([11846.0] * 18)
    target = min(
        canonical.target_candidates,
        key=lambda x: abs(x - 11845.626677302696),
    )

    a = canonical._predict_candidate(
        measured_raw=700.0,
        applied_dac=11846.0,
        requested_setpoint=450.0,
        target_dac=target,
        history_snapshot=history,
    )
    b = v3h.predict_candidate(
        measured_raw=700.0,
        applied_dac=11846.0,
        requested_setpoint=450.0,
        target_dac=target,
        history_snapshot=history,
    )

    assert a[0] == b[0]
    assert math.isclose(a[1], b[1], rel_tol=1e-12, abs_tol=1e-9)
    assert math.isclose(a[2], b[2], rel_tol=1e-12, abs_tol=1e-9)
    assert math.isclose(a[3], b[3], rel_tol=1e-12, abs_tol=1e-9)


def test_positive_state_disturbance_raises_future_prediction():
    c = make()
    history = tuple([11846.0] * 18)
    target = min(c.target_candidates, key=lambda x: abs(x - 11845.626677302696))

    c.disturbance_hat_raw_per_step = 0.0
    zero = c.predict_candidate(
        measured_raw=600.0,
        applied_dac=11846.0,
        requested_setpoint=450.0,
        target_dac=target,
        history_snapshot=history,
    )

    c.disturbance_hat_raw_per_step = 20.0
    positive = c.predict_candidate(
        measured_raw=600.0,
        applied_dac=11846.0,
        requested_setpoint=450.0,
        target_dac=target,
        history_snapshot=history,
    )

    assert positive[2] > zero[2]
    assert positive[3] > zero[3]


def test_rate_limit_remains_750_dac_per_update():
    c = make()
    command = c._rate_limited_command(11850.0, 0.0)
    assert command == 11100.0


def test_reset_disturbance():
    c = make()
    c.disturbance_hat_raw_per_step = 25.0
    c.last_innovation_raw = 30.0
    c.reset_disturbance()
    assert c.disturbance_hat_raw_per_step == 0.0
    assert c.last_innovation_raw == 0.0
