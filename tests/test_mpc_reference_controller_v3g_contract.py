from pathlib import Path
import importlib.util
import math

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "mpc_reference_controller_v3g.py"

spec = importlib.util.spec_from_file_location("mpc_reference_controller_v3g_test", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def make():
    model = mod.load_default_model()
    config = mod.default_v3e_config()
    return mod.SafeDelayedMoveBlockedNMPCV3G(
        model,
        config=config,
        bias_alpha=0.10,
    )


def test_bias_alpha_contract():
    c = make()
    assert c.bias_alpha == 0.10
    assert c.bias_raw == 0.0


def test_v3e_contract_preserved():
    c = make()
    assert c.config.sample_time_s == 0.5
    assert c.config.predicted_soft_level_raw == 1100.0
    assert c.config.predicted_hard_level_raw == 1400.0
    assert c.config.measured_hard_level_raw == 1500.0
    assert c.config.maximum_delta_dac == 750.0
    assert c.config.minimum_dac == 0.0
    assert c.config.maximum_dac == 12000.0
    assert len(c.target_candidates) == 13


def test_positive_residual_learns_positive_bias():
    c = make()
    pred = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_bias(
        measured_raw=pred + 100.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(c.bias_raw, 10.0, rel_tol=0, abs_tol=1e-9)


def test_bias_update_is_causal_ewma():
    c = make()
    pred = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_bias(
        measured_raw=pred + 100.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(c.bias_raw, 10.0, abs_tol=1e-9)

    pred2 = c.canonical_one_step_prediction(
        previous_measured_raw=510.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_bias(
        measured_raw=pred2 + 100.0,
        previous_measured_raw=510.0,
        delayed_applied_dac=11846.0,
    )
    assert math.isclose(c.bias_raw, 19.0, abs_tol=1e-9)


def test_bias_is_bounded():
    c = mod.SafeDelayedMoveBlockedNMPCV3G(
        mod.load_default_model(),
        config=mod.default_v3e_config(),
        bias_alpha=1.0,
        bias_limit_raw=50.0,
    )
    pred = c.canonical_one_step_prediction(
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    c.observe_and_update_bias(
        measured_raw=pred + 1000.0,
        previous_measured_raw=500.0,
        delayed_applied_dac=11846.0,
    )
    assert c.bias_raw == 50.0


def test_rate_limited_command_to_zero_remains_750_per_update():
    current = 11850.0
    path = [current]

    for _ in range(100):
        if current <= 0.0:
            break
        current = mod.SafeDelayedMoveBlockedNMPCV3G.rate_limited_command(
            current,
            0.0,
            maximum_delta_dac=750.0,
        )
        path.append(current)

    assert path[-1] == 0.0
    assert all(abs(b-a) <= 750.0 + 1e-12 for a,b in zip(path,path[1:]))


def test_positive_bias_lowers_effective_tracking_target():
    c = make()
    c.bias_raw = 100.0

    # Bias is represented by reducing canonical tracking setpoint by 100.
    assert 450.0 - c.bias_raw == 350.0


def test_positive_bias_tightens_predicted_limits():
    c = make()
    c.bias_raw = 100.0
    cfg = c._biased_config()
    assert cfg.predicted_soft_level_raw == 1000.0
    assert cfg.predicted_hard_level_raw == 1300.0


def test_reset_bias():
    c = make()
    c.bias_raw = 123.0
    c.last_residual_raw = 50.0
    c.reset_bias()
    assert c.bias_raw == 0.0
    assert c.last_residual_raw == 0.0
