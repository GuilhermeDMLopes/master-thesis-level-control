from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


DEFAULT_MODEL = Path(
    "models/mpc/deadzone-hammerstein-v1.json"
)
DEFAULT_OUTPUT = Path(
    "results/mpc/offline-nmpc-validation"
)


@dataclass(frozen=True)
class PlantParameters:
    tau_s: float
    baseline_raw: float
    deadzone_dac: float
    exponent: float
    equilibrium_gain: float


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    final_raw: float
    maximum_raw: float
    minimum_raw: float
    final_dac: float
    maximum_dac: float
    maximum_abs_delta_dac: float
    tail_mae_raw: float
    tail_bias_raw: float
    settling_time_s: float | None
    final_input_bias_estimate_dac: float
    hard_constraint_violations: int
    notes: list[str]


def step_model(
    y: float,
    u: float,
    parameters: PlantParameters,
    sample_time_s: float,
) -> float:
    a = math.exp(
        -sample_time_s
        / parameters.tau_s
    )
    nonlinear_input = max(
        0.0,
        u - parameters.deadzone_dac,
    ) ** parameters.exponent

    return (
        parameters.baseline_raw
        + a
        * (
            y
            - parameters.baseline_raw
        )
        + parameters.equilibrium_gain
        * (1.0 - a)
        * nonlinear_input
    )


def rate_limit(
    current: float,
    target: float,
    maximum_delta: float,
    minimum: float,
    maximum: float,
) -> float:
    delta = max(
        -maximum_delta,
        min(
            maximum_delta,
            target - current,
        ),
    )
    return max(
        minimum,
        min(
            maximum,
            current + delta,
        ),
    )


def model_sensitivity_to_input_bias(
    u: float,
    input_bias: float,
    parameters: PlantParameters,
    sample_time_s: float,
) -> float:
    effective = (
        u
        + input_bias
        - parameters.deadzone_dac
    )

    if effective <= 25.0:
        return 0.0

    a = math.exp(
        -sample_time_s
        / parameters.tau_s
    )

    return (
        parameters.equilibrium_gain
        * (1.0 - a)
        * parameters.exponent
        * (
            effective
            ** (
                parameters.exponent
                - 1.0
            )
        )
    )


class MoveBlockedNMPC:
    """
    Scalar nonlinear receding-horizon controller.

    Decision variable:
        a constant future DAC target over the prediction horizon.

    The real DAC is not allowed to jump to that target; the existing
    DAC rate limit is simulated inside the prediction. This is a
    move-blocked NMPC parameterization, appropriate as the first
    conservative offline implementation.
    """

    def __init__(
        self,
        *,
        model: PlantParameters,
        sample_time_s: float,
        setpoint_raw: float,
        minimum_dac: float,
        maximum_dac: float,
        maximum_delta_dac: float,
        prediction_horizon_s: float,
        target_grid_step_dac: float,
        predicted_soft_level_raw: float,
        predicted_hard_level_raw: float,
        tracking_weight: float,
        move_weight: float,
        soft_level_weight: float,
        terminal_weight: float,
        bias_adaptation_gain: float,
        maximum_bias_update_dac: float,
        maximum_abs_input_bias_dac: float,
    ) -> None:
        self.model = model
        self.sample_time_s = sample_time_s
        self.setpoint_raw = setpoint_raw
        self.minimum_dac = minimum_dac
        self.maximum_dac = maximum_dac
        self.maximum_delta_dac = maximum_delta_dac
        self.prediction_steps = max(
            1,
            int(
                round(
                    prediction_horizon_s
                    / sample_time_s
                )
            ),
        )
        self.predicted_soft_level_raw = (
            predicted_soft_level_raw
        )
        self.predicted_hard_level_raw = (
            predicted_hard_level_raw
        )
        self.tracking_weight = tracking_weight
        self.move_weight = move_weight
        self.soft_level_weight = soft_level_weight
        self.terminal_weight = terminal_weight

        self.bias_adaptation_gain = (
            bias_adaptation_gain
        )
        self.maximum_bias_update_dac = (
            maximum_bias_update_dac
        )
        self.maximum_abs_input_bias_dac = (
            maximum_abs_input_bias_dac
        )

        self.input_bias_dac = 0.0
        self.previous_prediction: (
            float | None
        ) = None
        self.previous_applied_dac: (
            float | None
        ) = None

        equilibrium_guess = self._implied_equilibrium_dac(
            setpoint_raw
        )

        grid_minimum = max(
            minimum_dac,
            min(
                model.deadzone_dac - 150.0,
                equilibrium_guess - 300.0,
            ),
        )
        grid_minimum = max(
            0.0,
            grid_minimum,
        )

        candidates = [minimum_dac]

        value = grid_minimum
        while value <= maximum_dac + 1e-9:
            candidates.append(
                min(
                    maximum_dac,
                    value,
                )
            )
            value += target_grid_step_dac

        candidates.extend(
            [
                model.deadzone_dac,
                equilibrium_guess,
                maximum_dac,
            ]
        )

        self.target_candidates = sorted(
            {
                round(
                    max(
                        minimum_dac,
                        min(
                            maximum_dac,
                            candidate,
                        ),
                    ),
                    9,
                )
                for candidate
                in candidates
            }
        )

    def _implied_equilibrium_dac(
        self,
        target_raw: float,
    ) -> float:
        delta = (
            target_raw
            - self.model.baseline_raw
        )

        if delta <= 0.0:
            return (
                self.model.deadzone_dac
            )

        effective = (
            delta
            / self.model.equilibrium_gain
        ) ** (
            1.0
            / self.model.exponent
        )

        return (
            self.model.deadzone_dac
            + effective
        )

    def update_bias_estimate(
        self,
        measured_raw: float,
    ) -> None:
        if (
            self.previous_prediction is None
            or self.previous_applied_dac
            is None
        ):
            return

        residual = (
            measured_raw
            - self.previous_prediction
        )

        sensitivity = (
            model_sensitivity_to_input_bias(
                self.previous_applied_dac,
                self.input_bias_dac,
                self.model,
                self.sample_time_s,
            )
        )

        if sensitivity <= 1e-6:
            return

        update = (
            self.bias_adaptation_gain
            * residual
            / sensitivity
        )

        update = max(
            -self.maximum_bias_update_dac,
            min(
                self.maximum_bias_update_dac,
                update,
            ),
        )

        self.input_bias_dac = max(
            -self.maximum_abs_input_bias_dac,
            min(
                self.maximum_abs_input_bias_dac,
                self.input_bias_dac
                + update,
            ),
        )

    def _predict_step(
        self,
        y: float,
        physical_dac: float,
    ) -> float:
        effective_dac = max(
            self.minimum_dac,
            min(
                self.maximum_dac
                + self.maximum_abs_input_bias_dac,
                physical_dac
                + self.input_bias_dac,
            ),
        )

        return step_model(
            y,
            effective_dac,
            self.model,
            self.sample_time_s,
        )

    def choose_action(
        self,
        measured_raw: float,
        current_dac: float,
    ) -> tuple[
        float,
        float,
        float,
    ]:
        self.update_bias_estimate(
            measured_raw
        )

        best: tuple[
            float,
            float,
        ] | None = None

        for target_dac in (
            self.target_candidates
        ):
            y = measured_raw
            u = current_dac
            previous_u = current_dac
            cost = 0.0
            feasible = True

            for _ in range(
                self.prediction_steps
            ):
                u = rate_limit(
                    u,
                    target_dac,
                    self.maximum_delta_dac,
                    self.minimum_dac,
                    self.maximum_dac,
                )

                y = self._predict_step(
                    y,
                    u,
                )

                if (
                    y
                    > self.predicted_hard_level_raw
                ):
                    feasible = False
                    break

                error = (
                    y
                    - self.setpoint_raw
                )
                move = (
                    u
                    - previous_u
                )

                cost += (
                    self.tracking_weight
                    * error
                    * error
                    + self.move_weight
                    * move
                    * move
                )

                if (
                    y
                    > self.predicted_soft_level_raw
                ):
                    excess = (
                        y
                        - self.predicted_soft_level_raw
                    )
                    cost += (
                        self.soft_level_weight
                        * excess
                        * excess
                    )

                previous_u = u

            if not feasible:
                continue

            terminal_error = (
                y
                - self.setpoint_raw
            )
            cost += (
                self.terminal_weight
                * terminal_error
                * terminal_error
            )

            score = (
                cost,
                target_dac,
            )

            if (
                best is None
                or score[0] < best[0]
            ):
                best = score

        if best is None:
            selected_target = (
                self.minimum_dac
            )
        else:
            selected_target = best[1]

        next_dac = rate_limit(
            current_dac,
            selected_target,
            self.maximum_delta_dac,
            self.minimum_dac,
            self.maximum_dac,
        )

        self.previous_applied_dac = (
            next_dac
        )
        self.previous_prediction = (
            self._predict_step(
                measured_raw,
                next_dac,
            )
        )

        return (
            next_dac,
            selected_target,
            self.input_bias_dac,
        )


def load_model(
    path: Path,
) -> PlantParameters:
    model = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    if (
        model.get("model_type")
        != "deadzone_hammerstein_first_order"
    ):
        raise RuntimeError(
            "Unexpected model type."
        )

    continuous = model[
        "continuous_time"
    ]

    parameters = PlantParameters(
        tau_s=float(
            continuous["tau_s"]
        ),
        baseline_raw=float(
            continuous[
                "baseline_raw_y0"
            ]
        ),
        deadzone_dac=float(
            continuous["deadzone_DAC"]
        ),
        exponent=float(
            continuous[
                "input_exponent_p"
            ]
        ),
        equilibrium_gain=float(
            continuous[
                "equilibrium_gain_G_raw_per_DAC_power_p"
            ]
        ),
    )

    if not (
        parameters.tau_s > 0.0
        and parameters.equilibrium_gain
        > 0.0
        and parameters.exponent
        > 0.0
    ):
        raise RuntimeError(
            "Model failed basic physical checks."
        )

    return parameters


def build_scenarios(
    nominal: PlantParameters,
) -> dict[
    str,
    tuple[
        PlantParameters,
        float,
    ],
]:
    """
    The second tuple field is measurement-noise sigma in raw counts.
    """
    return {
        "nominal": (
            nominal,
            0.0,
        ),
        "tau_fast_25pct": (
            PlantParameters(
                tau_s=0.75
                * nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                ),
                exponent=nominal.exponent,
                equilibrium_gain=(
                    nominal.equilibrium_gain
                ),
            ),
            0.0,
        ),
        "tau_slow_35pct": (
            PlantParameters(
                tau_s=1.35
                * nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                ),
                exponent=nominal.exponent,
                equilibrium_gain=(
                    nominal.equilibrium_gain
                ),
            ),
            0.0,
        ),
        "gain_high_20pct": (
            PlantParameters(
                tau_s=nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                ),
                exponent=nominal.exponent,
                equilibrium_gain=1.20
                * nominal.equilibrium_gain,
            ),
            0.0,
        ),
        "gain_low_20pct": (
            PlantParameters(
                tau_s=nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                ),
                exponent=nominal.exponent,
                equilibrium_gain=0.80
                * nominal.equilibrium_gain,
            ),
            0.0,
        ),
        "deadzone_minus_75": (
            PlantParameters(
                tau_s=nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                    - 75.0
                ),
                exponent=nominal.exponent,
                equilibrium_gain=(
                    nominal.equilibrium_gain
                ),
            ),
            0.0,
        ),
        "deadzone_plus_75": (
            PlantParameters(
                tau_s=nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                    + 75.0
                ),
                exponent=nominal.exponent,
                equilibrium_gain=(
                    nominal.equilibrium_gain
                ),
            ),
            0.0,
        ),
        "aggressive_combined": (
            PlantParameters(
                tau_s=0.75
                * nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                    - 75.0
                ),
                exponent=nominal.exponent,
                equilibrium_gain=1.20
                * nominal.equilibrium_gain,
            ),
            0.0,
        ),
        "sluggish_combined": (
            PlantParameters(
                tau_s=1.35
                * nominal.tau_s,
                baseline_raw=(
                    nominal.baseline_raw
                ),
                deadzone_dac=(
                    nominal.deadzone_dac
                    + 75.0
                ),
                exponent=nominal.exponent,
                equilibrium_gain=0.80
                * nominal.equilibrium_gain,
            ),
            0.0,
        ),
        "nominal_with_noise": (
            nominal,
            10.0,
        ),
    }


def settling_time(
    values: list[float],
    *,
    setpoint: float,
    band_raw: float,
    sample_time_s: float,
    required_duration_s: float,
) -> float | None:
    required = max(
        1,
        int(
            round(
                required_duration_s
                / sample_time_s
            )
        ),
    )

    for index in range(
        0,
        len(values)
        - required
        + 1,
    ):
        window = values[
            index :
            index + required
        ]

        if all(
            abs(value - setpoint)
            <= band_raw
            for value in window
        ):
            return (
                index
                * sample_time_s
            )

    return None


def simulate_scenario(
    *,
    name: str,
    plant: PlantParameters,
    noise_sigma_raw: float,
    controller_model: PlantParameters,
    args: argparse.Namespace,
    output_root: Path,
) -> ScenarioResult:
    controller = MoveBlockedNMPC(
        model=controller_model,
        sample_time_s=args.sample_time_s,
        setpoint_raw=args.setpoint_raw,
        minimum_dac=args.minimum_dac,
        maximum_dac=args.maximum_dac,
        maximum_delta_dac=(
            args.maximum_delta_dac
        ),
        prediction_horizon_s=(
            args.prediction_horizon_s
        ),
        target_grid_step_dac=(
            args.target_grid_step_dac
        ),
        predicted_soft_level_raw=(
            args.predicted_soft_level_raw
        ),
        predicted_hard_level_raw=(
            args.predicted_hard_level_raw
        ),
        tracking_weight=(
            args.tracking_weight
        ),
        move_weight=args.move_weight,
        soft_level_weight=(
            args.soft_level_weight
        ),
        terminal_weight=(
            args.terminal_weight
        ),
        bias_adaptation_gain=(
            args.bias_adaptation_gain
        ),
        maximum_bias_update_dac=(
            args.maximum_bias_update_dac
        ),
        maximum_abs_input_bias_dac=(
            args.maximum_abs_input_bias_dac
        ),
    )

    rng = random.Random(
        args.random_seed
        + sum(
            ord(character)
            for character
            in name
        )
    )

    steps = int(
        round(
            args.simulation_duration_s
            / args.sample_time_s
        )
    )

    y = plant.baseline_raw
    u = 0.0
    previous_u = u

    raw_values = []
    measured_values = []
    dac_values = []
    bias_values = []
    delta_values = []

    scenario_path = (
        output_root
        / f"{name}.csv"
    )

    with scenario_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.writer(
            stream,
            delimiter=";",
        )
        writer.writerow(
            [
                "time_s",
                "plant_raw",
                "measured_raw",
                "setpoint_raw",
                "applied_dac",
                "selected_target_dac",
                "delta_dac",
                "input_bias_estimate_dac",
            ]
        )

        for index in range(steps):
            measured = (
                y
                + (
                    rng.gauss(
                        0.0,
                        noise_sigma_raw,
                    )
                    if noise_sigma_raw
                    > 0.0
                    else 0.0
                )
            )

            (
                next_u,
                selected_target,
                bias_estimate,
            ) = controller.choose_action(
                measured,
                u,
            )

            delta_u = (
                next_u - u
            )

            y = step_model(
                y,
                next_u,
                plant,
                args.sample_time_s,
            )

            u = next_u

            raw_values.append(y)
            measured_values.append(
                measured
            )
            dac_values.append(u)
            bias_values.append(
                bias_estimate
            )
            delta_values.append(
                delta_u
            )

            writer.writerow(
                [
                    round(
                        index
                        * args.sample_time_s,
                        6,
                    ),
                    round(y, 9),
                    round(measured, 9),
                    args.setpoint_raw,
                    round(u, 9),
                    round(
                        selected_target,
                        9,
                    ),
                    round(
                        delta_u,
                        9,
                    ),
                    round(
                        bias_estimate,
                        9,
                    ),
                ]
            )

    tail_count = max(
        1,
        int(
            round(
                args.tail_metric_s
                / args.sample_time_s
            )
        ),
    )

    tail = raw_values[
        -tail_count:
    ]

    tail_errors = [
        value
        - args.setpoint_raw
        for value in tail
    ]

    constraints = 0

    if (
        max(dac_values)
        > args.maximum_dac
        + 1e-9
    ):
        constraints += 1

    if (
        min(dac_values)
        < args.minimum_dac
        - 1e-9
    ):
        constraints += 1

    if (
        max(
            abs(delta)
            for delta
            in delta_values
        )
        > args.maximum_delta_dac
        + 1e-9
    ):
        constraints += 1

    if (
        max(raw_values)
        > args.absolute_hard_level_raw
    ):
        constraints += 1

    settled = settling_time(
        raw_values,
        setpoint=args.setpoint_raw,
        band_raw=args.settling_band_raw,
        sample_time_s=args.sample_time_s,
        required_duration_s=(
            args.settling_hold_s
        ),
    )

    tail_mae = (
        statistics.fmean(
            abs(error)
            for error in tail_errors
        )
    )

    tail_bias = (
        statistics.fmean(
            tail_errors
        )
    )

    notes: list[str] = []

    if settled is None:
        notes.append(
            "did not satisfy settling criterion"
        )

    if (
        tail_mae
        > args.maximum_tail_mae_raw
    ):
        notes.append(
            "tail MAE above acceptance threshold"
        )

    if constraints:
        notes.append(
            "hard constraint violation"
        )

    passed = (
        constraints == 0
        and tail_mae
        <= args.maximum_tail_mae_raw
    )

    return ScenarioResult(
        name=name,
        passed=passed,
        final_raw=raw_values[-1],
        maximum_raw=max(raw_values),
        minimum_raw=min(raw_values),
        final_dac=dac_values[-1],
        maximum_dac=max(dac_values),
        maximum_abs_delta_dac=max(
            abs(delta)
            for delta
            in delta_values
        ),
        tail_mae_raw=tail_mae,
        tail_bias_raw=tail_bias,
        settling_time_s=settled,
        final_input_bias_estimate_dac=(
            bias_values[-1]
        ),
        hard_constraint_violations=(
            constraints
        ),
        notes=notes,
    )


def write_report(
    path: Path,
    results: list[ScenarioResult],
    args: argparse.Namespace,
) -> None:
    passed = sum(
        result.passed
        for result in results
    )

    lines = [
        "# Offline Nonlinear MPC Validation",
        "",
        "## Controller",
        "",
        "Move-blocked nonlinear receding-horizon MPC with:",
        "",
        f"- setpoint: {args.setpoint_raw:.1f} raw",
        f"- DAC range: {args.minimum_dac:.0f}..{args.maximum_dac:.0f}",
        (
            "- maximum DAC move: "
            f"{args.maximum_delta_dac:.0f} per "
            f"{args.sample_time_s:.3f} s"
        ),
        (
            "- prediction horizon: "
            f"{args.prediction_horizon_s:.1f} s"
        ),
        (
            "- predicted hard raw limit: "
            f"{args.predicted_hard_level_raw:.1f}"
        ),
        "- adaptive input-bias estimate for offset-free behavior",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Pass | Final raw | Max raw | Final DAC | "
        "Tail MAE | Settling s | Bias estimate DAC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for result in results:
        settling = (
            ""
            if result.settling_time_s
            is None
            else f"{result.settling_time_s:.1f}"
        )

        lines.append(
            f"| {result.name} | "
            f"{'YES' if result.passed else 'NO'} | "
            f"{result.final_raw:.2f} | "
            f"{result.maximum_raw:.2f} | "
            f"{result.final_dac:.1f} | "
            f"{result.tail_mae_raw:.2f} | "
            f"{settling} | "
            f"{result.final_input_bias_estimate_dac:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Passed scenarios: {passed}/{len(results)}.",
            "",
            "This is an offline controller-validation result only. "
            "Real MPC commissioning remains unauthorized until the "
            "controller implementation, safety fallback, and preserved-data "
            "tests are completed.",
            "",
        ]
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline robust simulation of a conservative move-blocked "
            "nonlinear MPC using the identified dead-zone Hammerstein model."
        )
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--sample-time-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--simulation-duration-s",
        type=float,
        default=90.0,
    )
    parser.add_argument(
        "--prediction-horizon-s",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--setpoint-raw",
        type=float,
        default=450.0,
    )

    parser.add_argument(
        "--minimum-dac",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--maximum-dac",
        type=float,
        default=12000.0,
    )
    parser.add_argument(
        "--maximum-delta-dac",
        type=float,
        default=150.0,
    )
    parser.add_argument(
        "--target-grid-step-dac",
        type=float,
        default=50.0,
    )

    parser.add_argument(
        "--predicted-soft-level-raw",
        type=float,
        default=650.0,
    )
    parser.add_argument(
        "--predicted-hard-level-raw",
        type=float,
        default=750.0,
    )
    parser.add_argument(
        "--absolute-hard-level-raw",
        type=float,
        default=800.0,
    )

    parser.add_argument(
        "--tracking-weight",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--move-weight",
        type=float,
        default=0.0002,
    )
    parser.add_argument(
        "--soft-level-weight",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--terminal-weight",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--bias-adaptation-gain",
        type=float,
        default=0.01,
    )
    parser.add_argument(
        "--maximum-bias-update-dac",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--maximum-abs-input-bias-dac",
        type=float,
        default=250.0,
    )

    parser.add_argument(
        "--tail-metric-s",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--maximum-tail-mae-raw",
        type=float,
        default=100.0,
    )
    parser.add_argument(
        "--settling-band-raw",
        type=float,
        default=50.0,
    )
    parser.add_argument(
        "--settling-hold-s",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    print("OFFLINE NONLINEAR MPC ROBUSTNESS VALIDATION")
    print("==========================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print("REAL PLANT ACCESS: NO")
    print()

    model = load_model(
        args.model
    )

    if (
        args.maximum_dac
        > 12000.0
    ):
        raise SystemExit(
            "This validation stage intentionally forbids "
            "MPC DAC above 12000."
        )

    scenarios = build_scenarios(
        model
    )

    args.output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    results: list[
        ScenarioResult
    ] = []

    for name, (
        plant,
        noise_sigma,
    ) in scenarios.items():
        print(
            f"Simulating {name}...",
            flush=True,
        )

        result = simulate_scenario(
            name=name,
            plant=plant,
            noise_sigma_raw=(
                noise_sigma
            ),
            controller_model=model,
            args=args,
            output_root=(
                args.output_root
            ),
        )

        results.append(
            result
        )

        print(
            "  "
            f"pass={result.passed} | "
            f"final={result.final_raw:.2f} | "
            f"max={result.maximum_raw:.2f} | "
            f"tail_MAE={result.tail_mae_raw:.2f} | "
            f"final_DAC={result.final_dac:.1f} | "
            f"bias={result.final_input_bias_estimate_dac:.2f}"
        )

    summary = {
        "controller": {
            "setpoint_raw": (
                args.setpoint_raw
            ),
            "minimum_dac": (
                args.minimum_dac
            ),
            "maximum_dac": (
                args.maximum_dac
            ),
            "maximum_delta_dac": (
                args.maximum_delta_dac
            ),
            "sample_time_s": (
                args.sample_time_s
            ),
            "prediction_horizon_s": (
                args.prediction_horizon_s
            ),
            "predicted_soft_level_raw": (
                args.predicted_soft_level_raw
            ),
            "predicted_hard_level_raw": (
                args.predicted_hard_level_raw
            ),
            "absolute_hard_level_raw": (
                args.absolute_hard_level_raw
            ),
        },
        "model": asdict(model),
        "results": [
            asdict(result)
            for result in results
        ],
    }

    summary_path = (
        args.output_root
        / "summary.json"
    )
    report_path = (
        args.output_root
        / "validation-report.md"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    write_report(
        report_path,
        results,
        args,
    )

    all_passed = all(
        result.passed
        for result in results
    )

    print()
    print("FINAL OFFLINE VALIDATION")
    print("------------------------")
    print(
        "Scenarios passed: "
        f"{sum(result.passed for result in results)}"
        f"/{len(results)}"
    )
    print(
        f"Summary: {summary_path}"
    )
    print(
        f"Report: {report_path}"
    )
    print()
    print(
        "OFFLINE MPC ROBUSTNESS: "
        f"{'PASSED' if all_passed else 'NOT YET PASSED'}"
    )
    print("REAL MPC AUTHORIZED: NO")

    if all_passed:
        print(
            "NEXT: controller contract tests and additive 4diac MPC implementation"
        )
        return 0

    print(
        "NEXT: inspect failed scenarios and retune offline only"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
