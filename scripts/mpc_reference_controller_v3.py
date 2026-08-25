from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DelayedPlantModel:
    baseline_raw: float
    deadzone_dac: float
    exponent: float
    equilibrium_gain: float
    sample_time_s: float
    transport_delay_steps: int
    transport_delay_s: float
    tau_s: float
    discrete_a: float
    discrete_b: float


@dataclass(frozen=True)
class MPCV3Config:
    sample_time_s: float = 0.5
    setpoint_raw: float = 450.0
    minimum_dac: float = 0.0
    maximum_dac: float = 12000.0
    maximum_delta_dac: float = 750.0
    prediction_horizon_s: float = 30.0
    predicted_soft_level_raw: float = 650.0
    predicted_hard_level_raw: float = 750.0
    measured_hard_level_raw: float = 800.0
    tracking_weight: float = 5.0
    move_weight: float = 0.00004
    soft_level_weight: float = 100.0
    terminal_weight: float = 10.0


@dataclass(frozen=True)
class MPCV3Output:
    command_enable: bool
    command_dac: float
    selected_target_dac: float
    tripped: bool
    trip_reason: str
    input_bias_estimate_dac: float
    predicted_max_raw: float
    predicted_final_raw: float
    delay_history_ready: bool
    delay_history_samples: int


def load_v3_model(path: Path) -> DelayedPlantModel:
    document = json.loads(path.read_text(encoding="utf-8"))

    if document.get("model_type") != "delayed_deadzone_hammerstein_first_order":
        raise ValueError("unexpected delayed MPC V3 model type")

    static = document["static_nonlinearity"]
    dynamic = document["dynamic_fit_500ms"]
    contract = document["controller_contract_proposal"]

    if int(contract["prediction_steps"]) != 60:
        raise ValueError("V3 model contract must use 60 prediction steps")
    if int(contract["target_candidates"]) != 13:
        raise ValueError("V3 model contract must use 13 target candidates")
    if float(contract["maximum_delta_dac_per_update"]) != 750.0:
        raise ValueError("V3 model contract must use 750 DAC/update")
    if int(contract["history_queue_length_samples"]) != int(
        dynamic["transport_delay_steps"]
    ):
        raise ValueError("V3 model contract queue length disagrees with fit")

    model = DelayedPlantModel(
        baseline_raw=float(dynamic["observation_state_floor_raw"]),
        deadzone_dac=float(static["deadzone_DAC"]),
        exponent=float(static["input_exponent_p"]),
        equilibrium_gain=float(
            static["equilibrium_gain_G_raw_per_DAC_power_p"]
        ),
        sample_time_s=float(contract["sample_time_s"]),
        transport_delay_steps=int(dynamic["transport_delay_steps"]),
        transport_delay_s=float(dynamic["transport_delay_s"]),
        tau_s=float(dynamic["tau_s"]),
        discrete_a=float(dynamic["discrete_a"]),
        discrete_b=float(dynamic["discrete_b_raw_per_DAC_power_p"]),
    )

    numeric_positive = (
        model.exponent,
        model.equilibrium_gain,
        model.sample_time_s,
        model.transport_delay_s,
        model.tau_s,
        model.discrete_b,
    )
    if not all(math.isfinite(value) and value > 0.0 for value in numeric_positive):
        raise ValueError("invalid positive V3 model parameter")
    if model.transport_delay_steps <= 0:
        raise ValueError("V3 transport-delay queue must be positive")
    if not math.isfinite(model.baseline_raw):
        raise ValueError("V3 baseline must be finite")
    if not math.isfinite(model.deadzone_dac) or model.deadzone_dac < 0.0:
        raise ValueError("V3 dead-zone must be finite and non-negative")
    if not (0.0 < model.discrete_a < 1.0):
        raise ValueError("V3 discrete state coefficient must be stable")

    expected_delay = model.sample_time_s * model.transport_delay_steps
    if not math.isclose(
        expected_delay,
        model.transport_delay_s,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("V3 delay seconds and queue length disagree")

    expected_a = math.exp(-model.sample_time_s / model.tau_s)
    expected_b = model.equilibrium_gain * (1.0 - expected_a)

    if not math.isclose(
        model.discrete_a,
        expected_a,
        rel_tol=0.0,
        abs_tol=5e-13,
    ):
        raise ValueError("V3 discrete a is inconsistent with tau")

    if not math.isclose(
        model.discrete_b,
        expected_b,
        rel_tol=0.0,
        abs_tol=5e-13,
    ):
        raise ValueError("V3 discrete b is inconsistent with static gain")

    return model


def delayed_plant_step(
    y_raw: float,
    delayed_dac: float,
    model: DelayedPlantModel,
) -> float:
    effective = max(0.0, delayed_dac - model.deadzone_dac)
    return (
        model.baseline_raw
        + model.discrete_a * (y_raw - model.baseline_raw)
        + model.discrete_b * effective**model.exponent
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


class SafeDelayedMoveBlockedNMPCV3:
    """
    Delay-aware fail-closed reference controller for MPC V3.

    The 18-sample queue stores actual AppliedDAC history. Candidate commands
    are appended behind already committed input, so predicted water already
    in transit cannot be cancelled by a new command.

    Bias adaptation is intentionally disabled in the first V3 implementation.
    The identified transport delay must not be misinterpreted as immediate
    input-model bias.
    """

    def __init__(
        self,
        model: DelayedPlantModel,
        config: MPCV3Config | None = None,
    ) -> None:
        self.model = model
        self.config = config or MPCV3Config()

        if not math.isclose(
            self.config.sample_time_s,
            self.model.sample_time_s,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("controller sample time must match V3 model")

        if self.config.maximum_dac > 12000.0:
            raise ValueError("V3 commissioning contract forbids DAC > 12000")
        if self.config.minimum_dac < 0.0:
            raise ValueError("V3 minimum DAC must be non-negative")
        if self.config.maximum_delta_dac != 750.0:
            raise ValueError("V3 move limit must remain 750 DAC/update")

        self._prediction_steps = int(
            round(
                self.config.prediction_horizon_s
                / self.config.sample_time_s
            )
        )
        if self._prediction_steps != 60:
            raise ValueError("V3 prediction horizon must be 60 x 500 ms")

        self._tripped = False
        self._trip_reason = ""

        self._delay_history: deque[float] = deque(
            [0.0] * self.model.transport_delay_steps,
            maxlen=self.model.transport_delay_steps,
        )
        self._delay_history_samples = 0

        equilibrium = self._implied_equilibrium_dac(
            self.config.setpoint_raw
        )

        # Exactly 13 implementation candidates:
        # zero + 11 values from dead-zone-250 through 12000 in 50-DAC
        # increments + exact equilibrium target.
        grid_start = max(
            self.config.minimum_dac,
            self.model.deadzone_dac - 250.0,
        )
        grid = [
            grid_start + 50.0 * index
            for index in range(11)
        ]
        candidates = [
            self.config.minimum_dac,
            *grid,
            equilibrium,
        ]

        self._target_candidates = sorted(
            {
                max(
                    self.config.minimum_dac,
                    min(self.config.maximum_dac, float(value)),
                )
                for value in candidates
            }
        )

        if len(self._target_candidates) != 13:
            raise ValueError(
                "V3 target candidate construction must yield exactly 13 values"
            )

    @property
    def tripped(self) -> bool:
        return self._tripped

    @property
    def trip_reason(self) -> str:
        return self._trip_reason

    @property
    def delay_history_ready(self) -> bool:
        return (
            self._delay_history_samples
            >= self.model.transport_delay_steps
        )

    @property
    def delay_history_samples(self) -> int:
        return min(
            self._delay_history_samples,
            self.model.transport_delay_steps,
        )

    @property
    def target_candidates(self) -> tuple[float, ...]:
        return tuple(self._target_candidates)

    def reset(self) -> None:
        # Reset clears the controller trip latch only. It deliberately does
        # NOT erase actual AppliedDAC history, because water already in transit
        # remains physically committed after a software reset.
        self._tripped = False
        self._trip_reason = ""

    def _implied_equilibrium_dac(self, target_raw: float) -> float:
        delta = target_raw - self.model.baseline_raw
        if delta <= 0.0:
            return self.model.deadzone_dac

        effective = (
            delta / self.model.equilibrium_gain
        ) ** (1.0 / self.model.exponent)

        return self.model.deadzone_dac + effective

    def _record_applied(self, applied_dac: float) -> None:
        if (
            math.isfinite(applied_dac)
            and self.config.minimum_dac
            <= applied_dac
            <= self.config.maximum_dac
        ):
            self._delay_history.append(float(applied_dac))
            self._delay_history_samples += 1

    def _output(
        self,
        *,
        command_enable: bool,
        command_dac: float,
        selected_target_dac: float,
        tripped: bool,
        trip_reason: str,
        predicted_max_raw: float,
        predicted_final_raw: float,
    ) -> MPCV3Output:
        return MPCV3Output(
            command_enable=command_enable,
            command_dac=command_dac,
            selected_target_dac=selected_target_dac,
            tripped=tripped,
            trip_reason=trip_reason,
            input_bias_estimate_dac=0.0,
            predicted_max_raw=predicted_max_raw,
            predicted_final_raw=predicted_final_raw,
            delay_history_ready=self.delay_history_ready,
            delay_history_samples=self.delay_history_samples,
        )

    def _trip(self, reason: str) -> MPCV3Output:
        self._tripped = True
        self._trip_reason = reason
        return self._output(
            command_enable=False,
            command_dac=0.0,
            selected_target_dac=0.0,
            tripped=True,
            trip_reason=reason,
            predicted_max_raw=float("nan"),
            predicted_final_raw=float("nan"),
        )

    def _disabled_output(self) -> MPCV3Output:
        return self._output(
            command_enable=False,
            command_dac=0.0,
            selected_target_dac=0.0,
            tripped=False,
            trip_reason="",
            predicted_max_raw=float("nan"),
            predicted_final_raw=float("nan"),
        )

    def _predict_candidate(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        requested_setpoint: float,
        target_dac: float,
        history_snapshot: tuple[float, ...],
    ) -> tuple[bool, float, float, float]:
        queue = deque(
            history_snapshot,
            maxlen=self.model.transport_delay_steps,
        )

        y = max(self.model.baseline_raw, measured_raw)
        command_u = applied_dac
        previous_command_u = applied_dac
        cost = 0.0
        predicted_max = y

        for _ in range(self._prediction_steps):
            command_u = _rate_limit(
                command_u,
                target_dac,
                self.config.maximum_delta_dac,
                self.config.minimum_dac,
                self.config.maximum_dac,
            )

            delayed_u = queue.popleft()
            queue.append(command_u)

            y = delayed_plant_step(
                y,
                delayed_u,
                self.model,
            )
            predicted_max = max(predicted_max, y)

            if (
                not math.isfinite(y)
                or y > self.config.predicted_hard_level_raw
            ):
                return False, float("inf"), predicted_max, y

            tracking_error = y - requested_setpoint
            move_value = command_u - previous_command_u

            cost += (
                self.config.tracking_weight
                * tracking_error
                * tracking_error
                + self.config.move_weight
                * move_value
                * move_value
            )

            if y > self.config.predicted_soft_level_raw:
                excess = y - self.config.predicted_soft_level_raw
                cost += (
                    self.config.soft_level_weight
                    * excess
                    * excess
                )

            previous_command_u = command_u

        terminal_error = y - requested_setpoint
        cost += (
            self.config.terminal_weight
            * terminal_error
            * terminal_error
        )

        return True, cost, predicted_max, y

    def step(
        self,
        *,
        measured_raw: float,
        applied_dac: float,
        enable_request: bool,
        external_healthy: bool,
        reset_request: bool = False,
        setpoint_raw: float | None = None,
    ) -> MPCV3Output:
        if reset_request:
            self.reset()

        try:
            numeric_measured = float(measured_raw)
            numeric_applied = float(applied_dac)
            requested_setpoint = (
                self.config.setpoint_raw
                if setpoint_raw is None
                else float(setpoint_raw)
            )
        except (TypeError, ValueError):
            return self._trip("NONFINITE_INPUT")

        if self._tripped:
            output = self._trip(self._trip_reason)
            self._record_applied(numeric_applied)
            return output

        if not enable_request:
            output = self._disabled_output()
            self._record_applied(numeric_applied)
            return output

        if not external_healthy:
            output = self._trip("EXTERNAL_HEALTH_FALSE")
            self._record_applied(numeric_applied)
            return output

        numeric_inputs = (
            numeric_measured,
            numeric_applied,
            requested_setpoint,
        )
        if not all(math.isfinite(value) for value in numeric_inputs):
            return self._trip("NONFINITE_INPUT")

        if numeric_measured < 0.0:
            output = self._trip("PV_NEGATIVE")
            self._record_applied(numeric_applied)
            return output

        if numeric_measured >= self.config.measured_hard_level_raw:
            output = self._trip("MEASURED_LEVEL_HARD_LIMIT")
            self._record_applied(numeric_applied)
            return output

        if not (
            self.config.minimum_dac
            <= numeric_applied
            <= self.config.maximum_dac
        ):
            return self._trip("APPLIED_DAC_OUTSIDE_STAGE_ENVELOPE")

        if not (
            0.0
            <= requested_setpoint
            < self.config.measured_hard_level_raw
        ):
            output = self._trip("SETPOINT_OUTSIDE_SAFE_RANGE")
            self._record_applied(numeric_applied)
            return output

        if not self.delay_history_ready:
            output = self._trip("DELAY_HISTORY_NOT_READY")
            self._record_applied(numeric_applied)
            return output

        history_snapshot = tuple(self._delay_history)

        best_cost: float | None = None
        best_target = 0.0
        best_max_raw = float("nan")
        best_final_raw = float("nan")

        for target_dac in self._target_candidates:
            feasible, cost, predicted_max, predicted_final = (
                self._predict_candidate(
                    measured_raw=numeric_measured,
                    applied_dac=numeric_applied,
                    requested_setpoint=requested_setpoint,
                    target_dac=target_dac,
                    history_snapshot=history_snapshot,
                )
            )

            if not feasible:
                continue

            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_target = target_dac
                best_max_raw = predicted_max
                best_final_raw = predicted_final

        if best_cost is None:
            output = self._trip("NO_FEASIBLE_PREDICTION")
            self._record_applied(numeric_applied)
            return output

        command_dac = _rate_limit(
            numeric_applied,
            best_target,
            self.config.maximum_delta_dac,
            self.config.minimum_dac,
            self.config.maximum_dac,
        )

        output = self._output(
            command_enable=True,
            command_dac=command_dac,
            selected_target_dac=best_target,
            tripped=False,
            trip_reason="",
            predicted_max_raw=best_max_raw,
            predicted_final_raw=best_final_raw,
        )

        # Record the physical AppliedDAC sample only after prediction. The
        # current sample becomes the newest queue element for the next cycle.
        self._record_applied(numeric_applied)
        return output
