"""Additive MPC V3G reference: V3E + causal output-bias correction.

This module does not modify V3/V3E. It reuses the authoritative V3 prediction
model/cost and applies an additive output-disturbance estimate to future
tracking and safety evaluation.

The bias estimate is causal:
    residual[k] = y[k] - yhat_one_step[k]
    bias[k] = (1-alpha)*bias[k-1] + alpha*residual[k]

For candidate evaluation, a positive output bias is equivalent to evaluating
the canonical model against:
    effective setpoint = requested_setpoint - bias
    effective soft limit = soft_limit - bias
    effective hard limit = hard_limit - bias

Predicted values reported by V3G are shifted back by +bias.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import math
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
V3_REFERENCE = ROOT / "scripts" / "mpc_reference_controller_v3.py"

_spec = importlib.util.spec_from_file_location(
    "mpc_reference_controller_v3_for_v3g",
    V3_REFERENCE,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load authoritative MPC V3 reference.")

v3 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v3
_spec.loader.exec_module(v3)

DEFAULT_BIAS_ALPHA = 0.10
DEFAULT_BIAS_LIMIT_RAW = 500.0


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


class SafeDelayedMoveBlockedNMPCV3G:
    """Additive output-bias wrapper around the authoritative V3 controller."""

    def __init__(
        self,
        model,
        config=None,
        *,
        bias_alpha: float = DEFAULT_BIAS_ALPHA,
        bias_limit_raw: float = DEFAULT_BIAS_LIMIT_RAW,
    ):
        if not (0.0 < bias_alpha <= 1.0):
            raise ValueError("bias_alpha must be in (0, 1].")
        if bias_limit_raw <= 0.0:
            raise ValueError("bias_limit_raw must be positive.")

        self.model = model
        self.config = config if config is not None else v3.MPCV3Config()
        self.bias_alpha = float(bias_alpha)
        self.bias_limit_raw = float(bias_limit_raw)
        self.bias_raw = 0.0
        self.last_residual_raw = 0.0

        self._canonical = v3.SafeDelayedMoveBlockedNMPCV3(
            model,
            config=self.config,
        )

    @property
    def target_candidates(self):
        return self._canonical.target_candidates

    def reset_bias(self) -> None:
        self.bias_raw = 0.0
        self.last_residual_raw = 0.0

    def _static_input(self, u: float) -> float:
        # Prefer any authoritative helper exposed by the canonical controller.
        for name in (
            "_hammerstein_input",
            "_static_nonlinearity",
            "_input_nonlinearity",
            "_effective_input",
            "_phi",
        ):
            fn = getattr(self._canonical, name, None)
            if callable(fn):
                try:
                    return float(fn(u))
                except TypeError:
                    pass

        deadzone = float(
            getattr(
                self.model,
                "deadzone_dac",
                getattr(self.model, "dead_zone_dac", 11750.0),
            )
        )
        exponent = float(getattr(self.model, "exponent", 1.2))
        gain = float(
            getattr(
                self.model,
                "gain",
                getattr(self.model, "hammerstein_gain", 0.680487474306),
            )
        )

        return gain * max(0.0, float(u) - deadzone) ** exponent

    def canonical_one_step_prediction(
        self,
        *,
        previous_measured_raw: float,
        delayed_applied_dac: float,
    ) -> float:
        baseline = float(self.model.baseline_raw)
        a = float(self.model.discrete_a)
        b = float(self.model.discrete_b)

        return (
            baseline
            + a * (float(previous_measured_raw) - baseline)
            + b * self._static_input(delayed_applied_dac)
        )

    def observe_and_update_bias(
        self,
        *,
        measured_raw: float,
        previous_measured_raw: float,
        delayed_applied_dac: float,
    ) -> float:
        predicted = self.canonical_one_step_prediction(
            previous_measured_raw=previous_measured_raw,
            delayed_applied_dac=delayed_applied_dac,
        )
        residual = float(measured_raw) - predicted
        self.last_residual_raw = residual

        updated = (
            (1.0 - self.bias_alpha) * self.bias_raw
            + self.bias_alpha * residual
        )

        self.bias_raw = _clamp(
            updated,
            -self.bias_limit_raw,
            self.bias_limit_raw,
        )
        return self.bias_raw

    def _biased_config(self):
        # Positive bias means the real output is above the canonical prediction.
        # Lower canonical safety thresholds by the bias so physical predictions
        # remain bounded after adding the disturbance estimate.
        soft = max(
            0.0,
            float(self.config.predicted_soft_level_raw) - self.bias_raw,
        )
        hard = max(
            soft,
            float(self.config.predicted_hard_level_raw) - self.bias_raw,
        )

        return dataclasses.replace(
            self.config,
            predicted_soft_level_raw=soft,
            predicted_hard_level_raw=hard,
        )

    def evaluate_candidate(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        requested_setpoint: float,
        target_dac: float,
        history_snapshot: Sequence[float],
    ):
        biased_config = self._biased_config()
        canonical = v3.SafeDelayedMoveBlockedNMPCV3(
            self.model,
            config=biased_config,
        )

        effective_setpoint = float(requested_setpoint) - self.bias_raw

        feasible, cost, predicted_max, predicted_final = canonical._predict_candidate(
            measured_raw=float(measured_raw),
            applied_dac=float(applied_dac),
            requested_setpoint=effective_setpoint,
            target_dac=float(target_dac),
            history_snapshot=tuple(float(x) for x in history_snapshot),
        )

        return (
            bool(feasible),
            float(cost),
            float(predicted_max) + self.bias_raw,
            float(predicted_final) + self.bias_raw,
        )

    def choose_target(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        requested_setpoint: float,
        history_snapshot: Sequence[float],
    ):
        evaluated = []

        for target in self.target_candidates:
            feasible, cost, predicted_max, predicted_final = self.evaluate_candidate(
                measured_raw=measured_raw,
                applied_dac=applied_dac,
                requested_setpoint=requested_setpoint,
                target_dac=target,
                history_snapshot=history_snapshot,
            )
            evaluated.append(
                {
                    "target": float(target),
                    "feasible": feasible,
                    "cost": cost,
                    "predicted_max": predicted_max,
                    "predicted_final": predicted_final,
                }
            )

        feasible = [x for x in evaluated if x["feasible"]]
        if not feasible:
            return None, evaluated

        return min(feasible, key=lambda x: x["cost"]), evaluated

    @staticmethod
    def rate_limited_command(
        applied_dac: float,
        target_dac: float,
        maximum_delta_dac: float = 750.0,
        minimum_dac: float = 0.0,
        maximum_dac: float = 12000.0,
    ) -> float:
        delta = _clamp(
            float(target_dac) - float(applied_dac),
            -float(maximum_delta_dac),
            float(maximum_delta_dac),
        )
        return _clamp(
            float(applied_dac) + delta,
            float(minimum_dac),
            float(maximum_dac),
        )

    def choose_command(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        requested_setpoint: float,
        history_snapshot: Sequence[float],
    ):
        best, evaluated = self.choose_target(
            measured_raw=measured_raw,
            applied_dac=applied_dac,
            requested_setpoint=requested_setpoint,
            history_snapshot=history_snapshot,
        )

        if best is None:
            return None, evaluated

        command = self.rate_limited_command(
            applied_dac=applied_dac,
            target_dac=best["target"],
            maximum_delta_dac=float(self.config.maximum_delta_dac),
            minimum_dac=float(self.config.minimum_dac),
            maximum_dac=float(self.config.maximum_dac),
        )

        result = dict(best)
        result["command_dac"] = command
        result["bias_raw"] = self.bias_raw
        result["last_residual_raw"] = self.last_residual_raw
        return result, evaluated


def load_default_model():
    return v3.load_v3_model(
        ROOT / "models" / "mpc" / "delayed-hammerstein-v3-candidate.json"
    )


def default_v3e_config():
    return v3.MPCV3Config(
        sample_time_s=0.5,
        setpoint_raw=450.0,
        minimum_dac=0.0,
        maximum_dac=12000.0,
        maximum_delta_dac=750.0,
        prediction_horizon_s=30.0,
        predicted_soft_level_raw=1100.0,
        predicted_hard_level_raw=1400.0,
        measured_hard_level_raw=1500.0,
        tracking_weight=5.0,
        move_weight=0.00004,
        soft_level_weight=100.0,
        terminal_weight=10.0,
    )
