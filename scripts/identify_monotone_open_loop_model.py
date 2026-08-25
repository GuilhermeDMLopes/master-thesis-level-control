from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DATA_ROOT = Path("data/raw")
DEFAULT_OUTPUT_ROOT = Path("results/mpc/monotone-open-loop-model")


@dataclass(frozen=True)
class Row:
    source: str
    phase: str
    t: float
    y: float
    u: float


@dataclass(frozen=True)
class Observation:
    source: str
    phase: str
    t: float
    y: float
    u: float
    dydt: float
    span_s: float


@dataclass(frozen=True)
class Fit:
    tau_s: float
    gain_raw_per_dac: float
    y_equilibrium_at_reference_raw: float
    u_reference_dac: float
    huber_loss: float
    derivative_rmse_raw_per_s: float
    derivative_median_abs_error_raw_per_s: float


def finite(value: float) -> bool:
    return math.isfinite(value)


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None

    text = value.strip()

    if not text:
        return None

    try:
        result = float(text)
    except ValueError:
        return None

    return result if finite(result) else None


def safe_bool(value: str | None) -> bool:
    if value is None:
        return False

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
    }


def discover_sources(data_root: Path) -> list[Path]:
    patterns = (
        "steady-calibration*/samples.csv",
        "steady-calibration-dac*/samples.csv",
        "local-identification*/local-identification.csv",
        "local-identification-v3-*/local-identification.csv",
    )

    discovered: dict[str, Path] = {}

    for pattern in patterns:
        for path in data_root.glob(pattern):
            if path.is_file():
                discovered[str(path.resolve())] = path

    return sorted(
        discovered.values(),
        key=lambda item: str(item).lower(),
    )


def read_source(path: Path) -> list[Row]:
    rows: list[Row] = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        reader = csv.DictReader(
            stream,
            delimiter=";",
        )

        if reader.fieldnames is None:
            return rows

        fieldnames = set(reader.fieldnames)

        if "rolling_median_level" in fieldnames:
            level_column = "rolling_median_level"
        elif "median9" in fieldnames:
            level_column = "median9"
        else:
            return rows

        required = {
            "phase",
            "elapsed_s",
            level_column,
            "applied_dac",
        }

        if not required.issubset(fieldnames):
            return rows

        for item in reader:
            t = safe_float(item.get("elapsed_s"))
            y = safe_float(item.get(level_column))
            u = safe_float(item.get("applied_dac"))

            if t is None or y is None or u is None:
                continue

            if (
                "applied_enable" in fieldnames
                and not safe_bool(
                    item.get("applied_enable")
                )
            ):
                continue

            rows.append(
                Row(
                    source=str(path),
                    phase=item.get("phase", "").strip(),
                    t=t,
                    y=y,
                    u=u,
                )
            )

    rows.sort(
        key=lambda sample: sample.t
    )

    return rows


def contiguous_plateaus(
    rows: list[Row],
) -> list[list[Row]]:
    if not rows:
        return []

    plateaus: list[list[Row]] = []
    current: list[Row] = [rows[0]]

    for row in rows[1:]:
        previous = current[-1]

        same_phase = (
            row.phase == previous.phase
        )
        same_dac = (
            abs(row.u - previous.u) < 0.5
        )
        monotonic_time = (
            row.t > previous.t
        )

        if (
            same_phase
            and same_dac
            and monotonic_time
        ):
            current.append(row)
        else:
            plateaus.append(current)
            current = [row]

    plateaus.append(current)

    return plateaus


def nearest_forward_sample(
    plateau: list[Row],
    start_index: int,
    target_time: float,
    minimum_time: float,
    maximum_time: float,
) -> Row | None:
    best: Row | None = None
    best_error = float("inf")

    for candidate in plateau[
        start_index + 1 :
    ]:
        if candidate.t < minimum_time:
            continue

        if candidate.t > maximum_time:
            break

        error = abs(
            candidate.t - target_time
        )

        if error < best_error:
            best = candidate
            best_error = error

    return best


def build_observations(
    sources: list[Path],
    *,
    minimum_dac: float,
    maximum_dac: float,
    minimum_level_raw: float,
    maximum_level_raw: float,
    derivative_window_s: float,
    observation_spacing_s: float,
) -> tuple[list[Observation], dict[str, int]]:
    observations: list[Observation] = []
    source_counts: dict[str, int] = {}

    for path in sources:
        rows = read_source(path)
        count_before = len(observations)

        for plateau in contiguous_plateaus(
            rows
        ):
            if len(plateau) < 3:
                continue

            dac = plateau[0].u

            if not (
                minimum_dac
                <= dac
                <= maximum_dac
            ):
                continue

            last_observation_time = (
                -float("inf")
            )

            for index, row in enumerate(
                plateau[:-1]
            ):
                if not (
                    minimum_level_raw
                    <= row.y
                    <= maximum_level_raw
                ):
                    continue

                if (
                    row.t
                    - last_observation_time
                    < observation_spacing_s
                ):
                    continue

                target_time = (
                    row.t
                    + derivative_window_s
                )
                minimum_time = (
                    row.t
                    + 0.75
                    * derivative_window_s
                )
                maximum_time = (
                    row.t
                    + 1.25
                    * derivative_window_s
                )

                future = nearest_forward_sample(
                    plateau,
                    index,
                    target_time,
                    minimum_time,
                    maximum_time,
                )

                if future is None:
                    continue

                if not (
                    minimum_level_raw
                    <= future.y
                    <= maximum_level_raw
                ):
                    continue

                span_s = (
                    future.t - row.t
                )

                if span_s <= 0:
                    continue

                observations.append(
                    Observation(
                        source=str(path),
                        phase=row.phase,
                        t=row.t,
                        y=row.y,
                        u=row.u,
                        dydt=(
                            future.y - row.y
                        )
                        / span_s,
                        span_s=span_s,
                    )
                )

                last_observation_time = (
                    row.t
                )

        source_counts[str(path)] = (
            len(observations)
            - count_before
        )

    return observations, source_counts


def weighted_line_fit(
    x: list[float],
    z: list[float],
    weights: list[float],
) -> tuple[float, float] | None:
    sw = sum(weights)

    if sw <= 0:
        return None

    sx = sum(
        weight * value
        for weight, value
        in zip(weights, x)
    )
    sz = sum(
        weight * value
        for weight, value
        in zip(weights, z)
    )
    sxx = sum(
        weight * value * value
        for weight, value
        in zip(weights, x)
    )
    sxz = sum(
        weight * x_value * z_value
        for weight, x_value, z_value
        in zip(weights, x, z)
    )

    denominator = (
        sw * sxx
        - sx * sx
    )

    if abs(denominator) < 1e-12:
        return None

    slope = (
        sw * sxz
        - sx * sz
    ) / denominator
    intercept = (
        sz - slope * sx
    ) / sw

    return intercept, slope


def robust_line_fit(
    x: list[float],
    z: list[float],
    *,
    huber_delta: float,
    iterations: int = 30,
) -> tuple[
    float,
    float,
    list[float],
] | None:
    weights = [
        1.0
        for _ in x
    ]

    result: tuple[
        float,
        float,
    ] | None = None

    for _ in range(iterations):
        result = weighted_line_fit(
            x,
            z,
            weights,
        )

        if result is None:
            return None

        intercept, slope = result
        residuals = [
            target
            - (
                intercept
                + slope * value
            )
            for value, target
            in zip(x, z)
        ]

        updated = []

        for residual in residuals:
            magnitude = abs(residual)

            if magnitude <= huber_delta:
                updated.append(1.0)
            else:
                updated.append(
                    huber_delta
                    / max(
                        magnitude,
                        1e-12,
                    )
                )

        maximum_change = max(
            abs(
                new - old
            )
            for new, old
            in zip(updated, weights)
        )

        weights = updated

        if maximum_change < 1e-6:
            break

    if result is None:
        return None

    return (
        result[0],
        result[1],
        weights,
    )


def huber_loss(
    residuals: Iterable[float],
    delta: float,
) -> float:
    total = 0.0

    for residual in residuals:
        magnitude = abs(residual)

        if magnitude <= delta:
            total += (
                0.5
                * residual
                * residual
            )
        else:
            total += (
                delta
                * (
                    magnitude
                    - 0.5 * delta
                )
            )

    return total


def prediction_rate(
    observation: Observation,
    *,
    tau_s: float,
    gain_raw_per_dac: float,
    y_equilibrium_at_reference_raw: float,
    u_reference_dac: float,
) -> float:
    equilibrium = (
        y_equilibrium_at_reference_raw
        + gain_raw_per_dac
        * (
            observation.u
            - u_reference_dac
        )
    )

    return -(
        observation.y
        - equilibrium
    ) / tau_s


def fit_model(
    observations: list[Observation],
    *,
    u_reference_dac: float,
    minimum_tau_s: float,
    maximum_tau_s: float,
    tau_step_s: float,
    minimum_reference_level_raw: float,
    maximum_reference_level_raw: float,
    huber_delta_raw_per_s: float,
) -> Fit:
    if len(observations) < 30:
        raise RuntimeError(
            "At least 30 derivative observations "
            "are required."
        )

    x = [
        observation.u
        - u_reference_dac
        for observation
        in observations
    ]

    best: Fit | None = None

    tau = minimum_tau_s

    while tau <= (
        maximum_tau_s + 1e-9
    ):
        z = [
            observation.dydt
            + observation.y / tau
            for observation
            in observations
        ]

        regression = robust_line_fit(
            x,
            z,
            huber_delta=(
                huber_delta_raw_per_s
            ),
        )

        if regression is not None:
            intercept, slope, _ = (
                regression
            )

            gain = (
                tau * slope
            )
            reference_level = (
                tau * intercept
            )

            if (
                gain > 0
                and minimum_reference_level_raw
                <= reference_level
                <= maximum_reference_level_raw
            ):
                predicted = [
                    prediction_rate(
                        observation,
                        tau_s=tau,
                        gain_raw_per_dac=gain,
                        y_equilibrium_at_reference_raw=reference_level,
                        u_reference_dac=u_reference_dac,
                    )
                    for observation
                    in observations
                ]

                residuals = [
                    observation.dydt
                    - estimate
                    for observation, estimate
                    in zip(
                        observations,
                        predicted,
                    )
                ]

                loss = huber_loss(
                    residuals,
                    huber_delta_raw_per_s,
                )
                rmse = math.sqrt(
                    statistics.fmean(
                        residual
                        * residual
                        for residual
                        in residuals
                    )
                )
                median_abs = (
                    statistics.median(
                        abs(residual)
                        for residual
                        in residuals
                    )
                )

                candidate = Fit(
                    tau_s=tau,
                    gain_raw_per_dac=gain,
                    y_equilibrium_at_reference_raw=reference_level,
                    u_reference_dac=u_reference_dac,
                    huber_loss=loss,
                    derivative_rmse_raw_per_s=rmse,
                    derivative_median_abs_error_raw_per_s=median_abs,
                )

                if (
                    best is None
                    or candidate.huber_loss
                    < best.huber_loss
                ):
                    best = candidate

        tau += tau_step_s

    if best is None:
        raise RuntimeError(
            "No physically monotone model "
            "satisfied the configured bounds."
        )

    return best


def evaluate_derivative_rmse(
    observations: list[Observation],
    fit: Fit,
) -> dict[str, float]:
    residuals = []

    for observation in observations:
        estimate = prediction_rate(
            observation,
            tau_s=fit.tau_s,
            gain_raw_per_dac=(
                fit.gain_raw_per_dac
            ),
            y_equilibrium_at_reference_raw=(
                fit.y_equilibrium_at_reference_raw
            ),
            u_reference_dac=(
                fit.u_reference_dac
            ),
        )
        residuals.append(
            observation.dydt
            - estimate
        )

    return {
        "count": len(residuals),
        "rmse_raw_per_s": (
            math.sqrt(
                statistics.fmean(
                    residual
                    * residual
                    for residual
                    in residuals
                )
            )
            if residuals
            else float("nan")
        ),
        "median_abs_error_raw_per_s": (
            statistics.median(
                abs(residual)
                for residual
                in residuals
            )
            if residuals
            else float("nan")
        ),
    }


def leave_one_source_out(
    observations: list[Observation],
    *,
    u_reference_dac: float,
    minimum_tau_s: float,
    maximum_tau_s: float,
    tau_step_s: float,
    minimum_reference_level_raw: float,
    maximum_reference_level_raw: float,
    huber_delta_raw_per_s: float,
) -> list[dict[str, object]]:
    sources = sorted(
        {
            observation.source
            for observation
            in observations
        }
    )

    reports = []

    for source in sources:
        validation = [
            observation
            for observation
            in observations
            if observation.source
            == source
        ]
        training = [
            observation
            for observation
            in observations
            if observation.source
            != source
        ]

        if (
            len(validation) < 5
            or len(training) < 30
        ):
            continue

        try:
            fit = fit_model(
                training,
                u_reference_dac=(
                    u_reference_dac
                ),
                minimum_tau_s=(
                    minimum_tau_s
                ),
                maximum_tau_s=(
                    maximum_tau_s
                ),
                tau_step_s=tau_step_s,
                minimum_reference_level_raw=(
                    minimum_reference_level_raw
                ),
                maximum_reference_level_raw=(
                    maximum_reference_level_raw
                ),
                huber_delta_raw_per_s=(
                    huber_delta_raw_per_s
                ),
            )
        except RuntimeError as error:
            reports.append(
                {
                    "source": source,
                    "status": "FIT_FAILED",
                    "message": str(error),
                }
            )
            continue

        validation_metrics = (
            evaluate_derivative_rmse(
                validation,
                fit,
            )
        )

        reports.append(
            {
                "source": source,
                "status": "OK",
                "training_observations": (
                    len(training)
                ),
                "validation_observations": (
                    len(validation)
                ),
                "fitted_tau_s": fit.tau_s,
                "fitted_gain_raw_per_dac": (
                    fit.gain_raw_per_dac
                ),
                "fitted_reference_level_raw": (
                    fit.y_equilibrium_at_reference_raw
                ),
                **validation_metrics,
            }
        )

    return reports


def model_dict(
    fit: Fit,
    *,
    mpc_sample_s: float,
    target_raw: float,
    source_counts: dict[str, int],
    cross_validation: list[
        dict[str, object]
    ],
) -> dict[str, object]:
    a = math.exp(
        -mpc_sample_s
        / fit.tau_s
    )
    b = (
        fit.gain_raw_per_dac
        * (1.0 - a)
    )

    equilibrium_dac = (
        fit.u_reference_dac
        + (
            target_raw
            - fit.y_equilibrium_at_reference_raw
        )
        / fit.gain_raw_per_dac
    )

    affine_constant = (
        1.0 - a
    ) * (
        fit.y_equilibrium_at_reference_raw
        - fit.gain_raw_per_dac
        * fit.u_reference_dac
    )

    return {
        "model_type": (
            "physically_constrained_monotone_first_order"
        ),
        "continuous_time": {
            "equation": (
                "dy/dt = -(y - "
                "(y_ref + K*(u-u_ref)))/tau"
            ),
            "tau_s": fit.tau_s,
            "K_raw_per_DAC": (
                fit.gain_raw_per_dac
            ),
            "u_ref_DAC": (
                fit.u_reference_dac
            ),
            "y_eq_at_u_ref_raw": (
                fit.y_equilibrium_at_reference_raw
            ),
        },
        "discrete_time_for_mpc": {
            "sample_time_s": mpc_sample_s,
            "equation": (
                "y[k+1] = a*y[k] + "
                "b*u[k] + c"
            ),
            "a": a,
            "b_raw_per_DAC": b,
            "c_raw": affine_constant,
        },
        "target_operating_point": {
            "target_raw": target_raw,
            "implied_equilibrium_DAC": (
                equilibrium_dac
            ),
        },
        "fit_metrics": {
            "derivative_RMSE_raw_per_s": (
                fit.derivative_rmse_raw_per_s
            ),
            "derivative_median_abs_error_raw_per_s": (
                fit.derivative_median_abs_error_raw_per_s
            ),
            "huber_loss": fit.huber_loss,
        },
        "source_observation_counts": (
            source_counts
        ),
        "leave_one_source_out_validation": (
            cross_validation
        ),
        "physical_constraints": {
            "positive_time_constant": True,
            "positive_static_gain": True,
        },
        "caution": (
            "This is an empirical physically constrained "
            "model in filtered raw-count coordinates. "
            "It is a candidate for offline MPC simulation, "
            "not authorization for real MPC commissioning."
        ),
    }


def write_report(
    path: Path,
    model: dict[str, object],
    *,
    sources: list[Path],
    observation_count: int,
) -> None:
    continuous = model[
        "continuous_time"
    ]
    discrete = model[
        "discrete_time_for_mpc"
    ]
    operating = model[
        "target_operating_point"
    ]
    metrics = model[
        "fit_metrics"
    ]

    lines = [
        "# Physically Constrained Open-Loop Model",
        "",
        "## Scope",
        "",
        "This identification is offline and uses the real "
        "open-loop / plateau datasets already collected in the laboratory.",
        "",
        "The model is constrained to have:",
        "",
        "- positive static gain from DAC to filtered raw level;",
        "- positive time constant;",
        "- a first-order monotone equilibrium relation.",
        "",
        "It deliberately does not reuse the unconstrained closed-loop ARX "
        "model that produced a negative physical gain.",
        "",
        "## Data",
        "",
        f"- Source files discovered: {len(sources)}",
        f"- Derivative observations used: {observation_count}",
        "",
    ]

    for source in sources:
        lines.append(
            f"- `{source.as_posix()}`"
        )

    lines.extend(
        [
            "",
            "## Continuous-time candidate",
            "",
            "```text",
            "dy/dt = -(y - (y_ref + K*(u-u_ref)))/tau",
            "```",
            "",
            f"- tau = {continuous['tau_s']:.6f} s",
            (
                "- K = "
                f"{continuous['K_raw_per_DAC']:.9f} raw/DAC"
            ),
            (
                "- u_ref = "
                f"{continuous['u_ref_DAC']:.3f} DAC"
            ),
            (
                "- y_eq(u_ref) = "
                f"{continuous['y_eq_at_u_ref_raw']:.3f} raw"
            ),
            "",
            "## MPC discrete-time form",
            "",
            "```text",
            "y[k+1] = a*y[k] + b*u[k] + c",
            "```",
            "",
            f"- Ts = {discrete['sample_time_s']:.6f} s",
            f"- a = {discrete['a']:.12f}",
            (
                "- b = "
                f"{discrete['b_raw_per_DAC']:.12f} raw/DAC"
            ),
            f"- c = {discrete['c_raw']:.9f} raw",
            "",
            "## Operating-point implication",
            "",
            (
                "- Target raw level = "
                f"{operating['target_raw']:.3f}"
            ),
            (
                "- Implied equilibrium DAC = "
                f"{operating['implied_equilibrium_DAC']:.3f}"
            ),
            "",
            "## Fit metrics",
            "",
            (
                "- Derivative RMSE = "
                f"{metrics['derivative_RMSE_raw_per_s']:.3f} raw/s"
            ),
            (
                "- Median absolute derivative error = "
                f"{metrics['derivative_median_abs_error_raw_per_s']:.3f} raw/s"
            ),
            "",
            "## Interpretation",
            "",
            "This model is intended as a low-order causal candidate "
            "for offline MPC development. The next stage must simulate "
            "the MPC against preserved real datasets before any real "
            "controller is enabled.",
            "",
        ]
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit a positive-gain, stable first-order model "
            "from preserved open-loop/plateau laboratory data. "
            "Offline only."
        )
    )

    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--minimum-dac",
        type=float,
        default=11600.0,
    )
    parser.add_argument(
        "--maximum-dac",
        type=float,
        default=14000.0,
    )
    parser.add_argument(
        "--minimum-level-raw",
        type=float,
        default=420.0,
    )
    parser.add_argument(
        "--maximum-level-raw",
        type=float,
        default=1200.0,
    )
    parser.add_argument(
        "--derivative-window-s",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--observation-spacing-s",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--u-reference-dac",
        type=float,
        default=11600.0,
    )
    parser.add_argument(
        "--minimum-tau-s",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--maximum-tau-s",
        type=float,
        default=60.0,
    )
    parser.add_argument(
        "--tau-step-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--minimum-reference-level-raw",
        type=float,
        default=350.0,
    )
    parser.add_argument(
        "--maximum-reference-level-raw",
        type=float,
        default=900.0,
    )
    parser.add_argument(
        "--huber-delta-raw-per-s",
        type=float,
        default=40.0,
    )
    parser.add_argument(
        "--mpc-sample-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--target-raw",
        type=float,
        default=450.0,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("MONOTONE OPEN-LOOP MPC MODEL IDENTIFICATION")
    print("===========================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print()

    sources = discover_sources(
        args.data_root
    )

    if not sources:
        raise SystemExit(
            "No supported laboratory datasets were "
            f"found below {args.data_root}."
        )

    observations, source_counts = (
        build_observations(
            sources,
            minimum_dac=args.minimum_dac,
            maximum_dac=args.maximum_dac,
            minimum_level_raw=(
                args.minimum_level_raw
            ),
            maximum_level_raw=(
                args.maximum_level_raw
            ),
            derivative_window_s=(
                args.derivative_window_s
            ),
            observation_spacing_s=(
                args.observation_spacing_s
            ),
        )
    )

    print(
        f"Source files discovered: {len(sources)}"
    )

    for source in sources:
        print(
            f"  {source} -> "
            f"{source_counts.get(str(source), 0)} observations"
        )

    print(
        f"Total derivative observations: "
        f"{len(observations)}"
    )

    fit = fit_model(
        observations,
        u_reference_dac=(
            args.u_reference_dac
        ),
        minimum_tau_s=args.minimum_tau_s,
        maximum_tau_s=args.maximum_tau_s,
        tau_step_s=args.tau_step_s,
        minimum_reference_level_raw=(
            args.minimum_reference_level_raw
        ),
        maximum_reference_level_raw=(
            args.maximum_reference_level_raw
        ),
        huber_delta_raw_per_s=(
            args.huber_delta_raw_per_s
        ),
    )

    cross_validation = (
        leave_one_source_out(
            observations,
            u_reference_dac=(
                args.u_reference_dac
            ),
            minimum_tau_s=(
                args.minimum_tau_s
            ),
            maximum_tau_s=(
                args.maximum_tau_s
            ),
            tau_step_s=args.tau_step_s,
            minimum_reference_level_raw=(
                args.minimum_reference_level_raw
            ),
            maximum_reference_level_raw=(
                args.maximum_reference_level_raw
            ),
            huber_delta_raw_per_s=(
                args.huber_delta_raw_per_s
            ),
        )
    )

    model = model_dict(
        fit,
        mpc_sample_s=args.mpc_sample_s,
        target_raw=args.target_raw,
        source_counts=source_counts,
        cross_validation=cross_validation,
    )

    args.output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = (
        args.output_root
        / "selected-physical-model.json"
    )
    report_path = (
        args.output_root
        / "identification-report.md"
    )

    model_path.write_text(
        json.dumps(
            model,
            indent=2,
        ),
        encoding="utf-8",
    )

    write_report(
        report_path,
        model,
        sources=sources,
        observation_count=len(
            observations
        ),
    )

    continuous = model[
        "continuous_time"
    ]
    discrete = model[
        "discrete_time_for_mpc"
    ]
    operating = model[
        "target_operating_point"
    ]

    print()
    print("SELECTED PHYSICAL MODEL")
    print("-----------------------")
    print(
        f"tau_s: "
        f"{continuous['tau_s']:.6f}"
    )
    print(
        "static gain raw/DAC: "
        f"{continuous['K_raw_per_DAC']:.9f}"
    )
    print(
        "equilibrium at reference raw: "
        f"{continuous['y_eq_at_u_ref_raw']:.6f}"
    )
    print(
        "reference DAC: "
        f"{continuous['u_ref_DAC']:.3f}"
    )
    print(
        "implied DAC at target raw: "
        f"{operating['implied_equilibrium_DAC']:.3f}"
    )
    print()
    print("DISCRETE MPC FORM")
    print("-----------------")
    print(
        f"Ts: "
        f"{discrete['sample_time_s']:.6f} s"
    )
    print(
        f"a: {discrete['a']:.12f}"
    )
    print(
        "b raw/DAC: "
        f"{discrete['b_raw_per_DAC']:.12f}"
    )
    print(
        f"c raw: "
        f"{discrete['c_raw']:.9f}"
    )
    print()
    print(
        "derivative RMSE raw/s: "
        f"{fit.derivative_rmse_raw_per_s:.6f}"
    )
    print(
        "median abs derivative error raw/s: "
        f"{fit.derivative_median_abs_error_raw_per_s:.6f}"
    )
    print()
    print(
        f"Model: {model_path}"
    )
    print(
        f"Report: {report_path}"
    )
    print()
    print("PHYSICAL GAIN POSITIVE: YES")
    print("MODEL DYNAMICS STABLE: YES")
    print("REAL MPC AUTHORIZED: NO")
    print(
        "NEXT: offline MPC simulation and preserved-data validation"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
