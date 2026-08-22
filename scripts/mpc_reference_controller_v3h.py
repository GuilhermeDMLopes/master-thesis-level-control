"""Additive MPC V3H reference controller.

V3H preserves the canonical V3/V3E plant model, fixed 13 target candidates,
transport delay, horizon, move limit and safety envelope.

The only control-model augmentation is a causal additive state/process
disturbance:

    d_hat[k] = (1-alpha)*d_hat[k-1] + alpha*(y[k] - yhat[k|k-1])

and every future prediction uses:

    y[k+1] = f_V3(y[k], u[k-delay]) + d_hat[k]

The selected alpha is 0.10 from the preserved 2026-08-22 real V3E evidence.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from collections import deque
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
V3_REFERENCE = ROOT / "scripts" / "mpc_reference_controller_v3.py"

_spec = importlib.util.spec_from_file_location(
    "mpc_reference_controller_v3_for_v3h",
    V3_REFERENCE,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load authoritative MPC V3 reference.")

v3 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v3
_spec.loader.exec_module(v3)

DEFAULT_DISTURBANCE_ALPHA = 0.10
DEFAULT_DISTURBANCE_LIMIT_RAW_PER_STEP = 100.0


def _clamp(value: float, low: float, high: float) -> float:
    return min(float(high), max(float(low), float(value)))


class SafeDelayedMoveBlockedNMPCV3H:
    """V3E-compatible MPC with causal additive process/state disturbance."""

    def __init__(
        self,
        model,
        config=None,
        *,
        disturbance_alpha: float = DEFAULT_DISTURBANCE_ALPHA,
        disturbance_limit_raw_per_step: float = DEFAULT_DISTURBANCE_LIMIT_RAW_PER_STEP,
    ):
        if not (0.0 < disturbance_alpha <= 1.0):
            raise ValueError("disturbance_alpha must be in (0, 1].")
        if disturbance_limit_raw_per_step <= 0.0:
            raise ValueError("disturbance_limit_raw_per_step must be positive.")

        self.model = model
        self.config = config if config is not None else default_v3e_config()
        self.disturbance_alpha = float(disturbance_alpha)
        self.disturbance_limit_raw_per_step = float(
            disturbance_limit_raw_per_step
        )

        self._canonical = v3.SafeDelayedMoveBlockedNMPCV3(
            model,
            config=self.config,
        )

        self._target_candidates = tuple(self._canonical.target_candidates)
        if len(self._target_candidates) != 13:
            raise ValueError("V3H must preserve exactly 13 canonical V3 targets.")

        self.disturbance_hat_raw_per_step = 0.0
        self.last_innovation_raw = 0.0

    @property
    def target_candidates(self):
        return self._target_candidates

    @property
    def equivalent_steady_shift_raw(self) -> float:
        a = float(self.model.discrete_a)
        if not (0.0 < a < 1.0):
            return float("nan")
        return self.disturbance_hat_raw_per_step / (1.0 - a)

    def reset_disturbance(self) -> None:
        self.disturbance_hat_raw_per_step = 0.0
        self.last_innovation_raw = 0.0

    def canonical_one_step_prediction(
        self,
        *,
        previous_measured_raw: float,
        delayed_applied_dac: float,
    ) -> float:
        return float(
            v3.delayed_plant_step(
                float(previous_measured_raw),
                float(delayed_applied_dac),
                self.model,
            )
        )

    def observe_and_update_disturbance(
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
        innovation = float(measured_raw) - predicted
        self.last_innovation_raw = innovation

        updated = (
            (1.0 - self.disturbance_alpha)
            * self.disturbance_hat_raw_per_step
            + self.disturbance_alpha
            * innovation
        )

        self.disturbance_hat_raw_per_step = _clamp(
            updated,
            -self.disturbance_limit_raw_per_step,
            self.disturbance_limit_raw_per_step,
        )

        return self.disturbance_hat_raw_per_step

    def input_effect_raw_per_step(self, dac: float) -> float:
        baseline = float(self.model.baseline_raw)
        return max(
            0.0,
            float(
                v3.delayed_plant_step(
                    baseline,
                    float(dac),
                    self.model,
                )
            )
            - baseline,
        )

    def _rate_limited_command(
        self,
        applied_dac: float,
        target_dac: float,
    ) -> float:
        return float(
            v3._rate_limit(
                float(applied_dac),
                float(target_dac),
                float(self.config.maximum_delta_dac),
                float(self.config.minimum_dac),
                float(self.config.maximum_dac),
            )
        )

    def predict_candidate(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        requested_setpoint: float,
        target_dac: float,
        history_snapshot: Sequence[float],
    ):
        if len(history_snapshot) != int(self.model.transport_delay_steps):
            raise ValueError(
                f"Expected {self.model.transport_delay_steps} AppliedDAC "
                f"history samples, got {len(history_snapshot)}."
            )

        queue = deque(
            (float(x) for x in history_snapshot),
            maxlen=int(self.model.transport_delay_steps),
        )

        y = max(float(self.model.baseline_raw), float(measured_raw))
        command_u = float(applied_dac)
        previous_command_u = float(applied_dac)
        cost = 0.0
        predicted_max = y

        prediction_steps = int(
            round(
                float(self.config.prediction_horizon_s)
                / float(self.config.sample_time_s)
            )
        )

        if prediction_steps != 60:
            raise ValueError(
                f"V3H implementation contract expects 60 prediction steps, "
                f"found {prediction_steps}."
            )

        for _ in range(prediction_steps):
            command_u = self._rate_limited_command(
                command_u,
                target_dac,
            )

            delayed_u = queue.popleft()
            queue.append(command_u)

            y = (
                float(
                    v3.delayed_plant_step(
                        y,
                        delayed_u,
                        self.model,
                    )
                )
                + self.disturbance_hat_raw_per_step
            )

            predicted_max = max(predicted_max, y)

            if (
                not math.isfinite(y)
                or y > float(self.config.predicted_hard_level_raw)
            ):
                return False, float("inf"), predicted_max, y

            tracking_error = y - float(requested_setpoint)
            move_value = command_u - previous_command_u

            cost += (
                float(self.config.tracking_weight)
                * tracking_error
                * tracking_error
                + float(self.config.move_weight)
                * move_value
                * move_value
            )

            if y > float(self.config.predicted_soft_level_raw):
                excess = y - float(self.config.predicted_soft_level_raw)
                cost += (
                    float(self.config.soft_level_weight)
                    * excess
                    * excess
                )

            previous_command_u = command_u

        terminal_error = y - float(requested_setpoint)
        cost += (
            float(self.config.terminal_weight)
            * terminal_error
            * terminal_error
        )

        return True, cost, predicted_max, y

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
            feasible, cost, predicted_max, predicted_final = self.predict_candidate(
                measured_raw=measured_raw,
                applied_dac=applied_dac,
                requested_setpoint=requested_setpoint,
                target_dac=target,
                history_snapshot=history_snapshot,
            )

            evaluated.append(
                {
                    "target": float(target),
                    "feasible": bool(feasible),
                    "cost": float(cost),
                    "predicted_max": float(predicted_max),
                    "predicted_final": float(predicted_final),
                }
            )

        feasible = [x for x in evaluated if x["feasible"]]
        if not feasible:
            return None, evaluated

        return min(feasible, key=lambda x: x["cost"]), evaluated

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

        command = self._rate_limited_command(
            applied_dac,
            best["target"],
        )

        result = dict(best)
        result["command_dac"] = command
        result["disturbance_hat_raw_per_step"] = (
            self.disturbance_hat_raw_per_step
        )
        result["equivalent_steady_shift_raw"] = (
            self.equivalent_steady_shift_raw
        )
        result["last_innovation_raw"] = self.last_innovation_raw

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
