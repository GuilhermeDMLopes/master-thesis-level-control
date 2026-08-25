from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlantModel:
    tau_s: float
    baseline_raw: float
    deadzone_dac: float
    exponent: float
    equilibrium_gain: float


@dataclass(frozen=True)
class MPCConfig:
    sample_time_s: float = 0.1
    setpoint_raw: float = 450.0
    minimum_dac: float = 0.0
    maximum_dac: float = 12000.0
    maximum_delta_dac: float = 150.0

    prediction_horizon_s: float = 20.0
    target_grid_step_dac: float = 50.0

    predicted_soft_level_raw: float = 650.0
    predicted_hard_level_raw: float = 750.0
    measured_hard_level_raw: float = 800.0

    tracking_weight: float = 1.0
    move_weight: float = 0.0002
    soft_level_weight: float = 20.0
    terminal_weight: float = 10.0

    bias_adaptation_gain: float = 0.01
    maximum_bias_update_dac: float = 5.0
    maximum_abs_input_bias_dac: float = 250.0


@dataclass(frozen=True)
class MPCOutput:
    command_enable: bool
    command_dac: float
    selected_target_dac: float
    tripped: bool
    trip_reason: str
    input_bias_estimate_dac: float
    predicted_max_raw: float
    predicted_final_raw: float


def load_model(path: Path) -> PlantModel:
    document = json.loads(path.read_text(encoding="utf-8"))

    if document.get("model_type") != "deadzone_hammerstein_first_order":
        raise ValueError("unexpected MPC model type")

    continuous = document["continuous_time"]

    model = PlantModel(
        tau_s=float(continuous["tau_s"]),
        baseline_raw=float(continuous["baseline_raw_y0"]),
        deadzone_dac=float(continuous["deadzone_DAC"]),
        exponent=float(continuous["input_exponent_p"]),
        equilibrium_gain=float(
            continuous["equilibrium_gain_G_raw_per_DAC_power_p"]
        ),
    )

    if not math.isfinite(model.tau_s) or model.tau_s <= 0.0:
        raise ValueError("tau must be finite and positive")

    if (
        not math.isfinite(model.equilibrium_gain)
        or model.equilibrium_gain <= 0.0
    ):
        raise ValueError("equilibrium gain must be finite and positive")

    if not math.isfinite(model.exponent) or model.exponent <= 0.0:
        raise ValueError("input exponent must be finite and positive")

    if (
        not math.isfinite(model.deadzone_dac)
        or model.deadzone_dac < 0.0
    ):
        raise ValueError("dead-zone DAC must be finite and non-negative")

    return model


def plant_step(
    y_raw: float,
    dac: float,
    model: PlantModel,
    sample_time_s: float,
) -> float:
    a = math.exp(-sample_time_s / model.tau_s)
    effective = max(0.0, dac - model.deadzone_dac)
    return (
        model.baseline_raw
        + a * (y_raw - model.baseline_raw)
        + model.equilibrium_gain
        * (1.0 - a)
        * effective**model.exponent
    )


def _rate_limit(
    current: float,
    target: float,
    maximum_delta: float,
    lower: float,
    upper: float,
) -> float:
    delta = max(
        -maximum_delta,
        min(maximum_delta, target - current),
    )
    return max(lower, min(upper, current + delta))


class SafeMoveBlockedNMPC:
    """
    Reference controller contract for the first real MPC implementation.

    Fail-closed inputs:
      * non-finite PV / AppliedDAC / SP
      * PV >= measured hard limit
      * external health false
      * AppliedDAC outside the approved stage envelope
      * no feasible predicted candidate

    Disable is not a trip:
      ENABLE_REQUEST=False -> command_enable=False, command_dac=0.
    """

    def __init__(
        self,
        model: PlantModel,
        config: MPCConfig | None = None,
    ) -> None:
        self.model = model
        self.config = config or MPCConfig()

        if self.config.maximum_dac > 12000.0:
            raise ValueError(
                "first MPC commissioning contract forbids DAC > 12000"
            )

        if self.config.maximum_delta_dac <= 0.0:
            raise ValueError("maximum DAC move must be positive")

        self._tripped = False
        self._trip_reason = ""
        self._input_bias_dac = 0.0
        self._previous_prediction: float | None = None
        self._previous_applied_dac: float | None = None

        self._prediction_steps = max(
            1,
            int(
                round(
                    self.config.prediction_horizon_s
                    / self.config.sample_time_s
                )
            ),
        )

        equilibrium_guess = self._implied_equilibrium_dac(
            self.config.setpoint_raw
        )

        grid_minimum = max(
            self.config.minimum_dac,
            min(
                self.model.deadzone_dac - 150.0,
                equilibrium_guess - 300.0,
            ),
        )

        candidates = [self.config.minimum_dac]
        value = grid_minimum

        while value <= self.config.maximum_dac + 1e-9:
            candidates.append(value)
            value += self.config.target_grid_step_dac

        candidates.extend(
            [
                self.model.deadzone_dac,
                equilibrium_guess,
                self.config.maximum_dac,
            ]
        )

        self._target_candidates = sorted(
            {
                max(
                    self.config.minimum_dac,
                    min(self.config.maximum_dac, float(candidate)),
                )
                for candidate in candidates
            }
        )

    @property
    def tripped(self) -> bool:
        return self._tripped

    @property
    def trip_reason(self) -> str:
        return self._trip_reason

    @property
    def input_bias_estimate_dac(self) -> float:
        return self._input_bias_dac

    def reset(self) -> None:
        self._tripped = False
        self._trip_reason = ""
        self._input_bias_dac = 0.0
        self._previous_prediction = None
        self._previous_applied_dac = None

    def _trip(self, reason: str) -> MPCOutput:
        self._tripped = True
        self._trip_reason = reason
        return MPCOutput(
            command_enable=False,
            command_dac=0.0,
            selected_target_dac=0.0,
            tripped=True,
            trip_reason=reason,
            input_bias_estimate_dac=self._input_bias_dac,
            predicted_max_raw=float("nan"),
            predicted_final_raw=float("nan"),
        )

    def _disabled_output(self) -> MPCOutput:
        self._previous_prediction = None
        self._previous_applied_dac = None
        self._input_bias_dac = 0.0

        return MPCOutput(
            command_enable=False,
            command_dac=0.0,
            selected_target_dac=0.0,
            tripped=False,
            trip_reason="",
            input_bias_estimate_dac=0.0,
            predicted_max_raw=float("nan"),
            predicted_final_raw=float("nan"),
        )

    def _implied_equilibrium_dac(self, target_raw: float) -> float:
        delta = target_raw - self.model.baseline_raw

        if delta <= 0.0:
            return self.model.deadzone_dac

        effective = (
            delta / self.model.equilibrium_gain
        ) ** (1.0 / self.model.exponent)

        return self.model.deadzone_dac + effective

    def _model_sensitivity_to_input_bias(
        self,
        applied_dac: float,
    ) -> float:
        effective = (
            applied_dac
            + self._input_bias_dac
            - self.model.deadzone_dac
        )

        if effective <= 25.0:
            return 0.0

        a = math.exp(
            -self.config.sample_time_s / self.model.tau_s
        )

        return (
            self.model.equilibrium_gain
            * (1.0 - a)
            * self.model.exponent
            * effective ** (self.model.exponent - 1.0)
        )

    def _update_bias_estimate(self, measured_raw: float) -> None:
        if (
            self._previous_prediction is None
            or self._previous_applied_dac is None
        ):
            return

        residual = measured_raw - self._previous_prediction
        sensitivity = self._model_sensitivity_to_input_bias(
            self._previous_applied_dac
        )

        if sensitivity <= 1e-6:
            return

        update = (
            self.config.bias_adaptation_gain
            * residual
            / sensitivity
        )

        update = max(
            -self.config.maximum_bias_update_dac,
            min(self.config.maximum_bias_update_dac, update),
        )

        self._input_bias_dac = max(
            -self.config.maximum_abs_input_bias_dac,
            min(
                self.config.maximum_abs_input_bias_dac,
                self._input_bias_dac + update,
            ),
        )

    def _predict_step(self, y_raw: float, physical_dac: float) -> float:
        effective_dac = max(
            self.config.minimum_dac,
            min(
                self.config.maximum_dac
                + self.config.maximum_abs_input_bias_dac,
                physical_dac + self._input_bias_dac,
            ),
        )

        return plant_step(
            y_raw,
            effective_dac,
            self.model,
            self.config.sample_time_s,
        )

    def step(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        enable_request: bool,
        external_healthy: bool,
        reset_request: bool = False,
        setpoint_raw: float | None = None,
    ) -> MPCOutput:
        if reset_request:
            self.reset()

        if self._tripped:
            return self._trip(self._trip_reason)

        if not enable_request:
            return self._disabled_output()

        if not external_healthy:
            return self._trip("EXTERNAL_HEALTH_FALSE")

        requested_setpoint = (
            self.config.setpoint_raw
            if setpoint_raw is None
            else float(setpoint_raw)
        )

        numeric_inputs = (
            float(measured_raw),
            float(applied_dac),
            requested_setpoint,
        )

        if not all(math.isfinite(value) for value in numeric_inputs):
            return self._trip("NONFINITE_INPUT")

        if measured_raw < 0.0:
            return self._trip("PV_NEGATIVE")

        if measured_raw >= self.config.measured_hard_level_raw:
            return self._trip("MEASURED_LEVEL_HARD_LIMIT")

        if not (
            self.config.minimum_dac
            <= applied_dac
            <= self.config.maximum_dac
        ):
            return self._trip("APPLIED_DAC_OUTSIDE_STAGE_ENVELOPE")

        if not (
            0.0
            <= requested_setpoint
            < self.config.measured_hard_level_raw
        ):
            return self._trip("SETPOINT_OUTSIDE_SAFE_RANGE")

        self._update_bias_estimate(measured_raw)

        try:

            best_cost: float | None = None
            best_target = 0.0
            best_max_raw = float("nan")
            best_final_raw = float("nan")

            for target_dac in self._target_candidates:
                y = measured_raw
                u = applied_dac
                previous_u = applied_dac
                cost = 0.0
                predicted_max = y
                feasible = True

                for _ in range(self._prediction_steps):
                    u = _rate_limit(
                        u,
                        target_dac,
                        self.config.maximum_delta_dac,
                        self.config.minimum_dac,
                        self.config.maximum_dac,
                    )

                    y = self._predict_step(y, u)
                    predicted_max = max(predicted_max, y)

                    if (
                        not math.isfinite(y)
                        or y > self.config.predicted_hard_level_raw
                    ):
                        feasible = False
                        break

                    error = y - requested_setpoint
                    move = u - previous_u

                    cost += (
                        self.config.tracking_weight * error * error
                        + self.config.move_weight * move * move
                    )

                    if y > self.config.predicted_soft_level_raw:
                        excess = y - self.config.predicted_soft_level_raw
                        cost += (
                            self.config.soft_level_weight
                            * excess
                            * excess
                        )

                    previous_u = u

                if not feasible:
                    continue

                terminal_error = y - requested_setpoint
                cost += (
                    self.config.terminal_weight
                    * terminal_error
                    * terminal_error
                )

                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_target = target_dac
                    best_max_raw = predicted_max
                    best_final_raw = y

            if best_cost is None:
                return self._trip("NO_FEASIBLE_PREDICTION")

            command_dac = _rate_limit(
                applied_dac,
                best_target,
                self.config.maximum_delta_dac,
                self.config.minimum_dac,
                self.config.maximum_dac,
            )

            self._previous_applied_dac = command_dac
            self._previous_prediction = self._predict_step(
                measured_raw,
                command_dac,
            )

            return MPCOutput(
                command_enable=True,
                command_dac=command_dac,
                selected_target_dac=best_target,
                tripped=False,
                trip_reason="",
                input_bias_estimate_dac=self._input_bias_dac,
                predicted_max_raw=best_max_raw,
                predicted_final_raw=best_final_raw,
            )
        finally:
            pass
