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
DEFAULT_OUTPUT_ROOT = Path("results/mpc/deadzone-hammerstein-model")


@dataclass(frozen=True)
class Sample:
    t: float
    y: float
    u: float


@dataclass(frozen=True)
class Segment:
    source: str
    samples: tuple[Sample, ...]


@dataclass(frozen=True)
class Candidate:
    tau_s: float
    deadzone_dac: float
    exponent: float
    equilibrium_gain: float
    train_rmse_raw: float
    train_mae_raw: float
    validation_rmse_raw: float
    validation_mae_raw: float
    validation_bias_raw: float
    validation_max_abs_error_raw: float


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
    return result if math.isfinite(result) else None


def safe_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"true", "1", "yes"}


def discover_sources(data_root: Path) -> list[Path]:
    patterns = (
        "steady-calibration*/samples.csv",
        "steady-calibration-dac*/samples.csv",
        "local-identification*/local-identification.csv",
        "local-identification-v3-*/local-identification.csv",
    )

    found: dict[str, Path] = {}

    for pattern in patterns:
        for path in data_root.glob(pattern):
            if path.is_file():
                found[str(path.resolve())] = path

    return sorted(found.values(), key=lambda path: str(path).lower())


def read_active_samples(
    path: Path,
    *,
    minimum_raw: float,
    maximum_raw: float,
) -> list[Sample]:
    rows: list[Sample] = []

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")

        if reader.fieldnames is None:
            return rows

        fields = set(reader.fieldnames)

        if "rolling_median_level" in fields:
            level_column = "rolling_median_level"
        elif "median9" in fields:
            level_column = "median9"
        else:
            return rows

        if not {
            "elapsed_s",
            level_column,
            "applied_dac",
        }.issubset(fields):
            return rows

        for item in reader:
            if (
                "applied_enable" in fields
                and not safe_bool(item.get("applied_enable"))
            ):
                continue

            t = safe_float(item.get("elapsed_s"))
            y = safe_float(item.get(level_column))
            u = safe_float(item.get("applied_dac"))

            if t is None or y is None or u is None:
                continue

            if not minimum_raw <= y <= maximum_raw:
                continue

            rows.append(Sample(t=t, y=y, u=u))

    rows.sort(key=lambda row: row.t)
    return rows


def make_segments(
    source: Path,
    samples: list[Sample],
    *,
    maximum_gap_s: float,
    minimum_segment_samples: int,
) -> list[Segment]:
    if not samples:
        return []

    groups: list[list[Sample]] = [[samples[0]]]

    for sample in samples[1:]:
        previous = groups[-1][-1]
        dt = sample.t - previous.t

        if 0.0 < dt <= maximum_gap_s:
            groups[-1].append(sample)
        else:
            groups.append([sample])

    result = []

    for group in groups:
        if len(group) >= minimum_segment_samples:
            result.append(
                Segment(
                    source=str(source),
                    samples=tuple(group),
                )
            )

    return result


def input_feature(
    u: float,
    *,
    deadzone_dac: float,
    exponent: float,
) -> float:
    return max(0.0, u - deadzone_dac) ** exponent


def build_linear_gain_terms(
    segments: list[Segment],
    *,
    tau_s: float,
    deadzone_dac: float,
    exponent: float,
    baseline_raw: float,
) -> tuple[list[float], list[float]]:
    """
    For fixed tau/deadzone/exponent:

        y[k+1] = y0 + a*(y[k]-y0)
                 + G*(1-a)*phi(u[k])

    A full simulated trajectory is affine in G:

        y_hat[k] = base[k] + G*basis[k]

    This function returns (target-base, basis) pairs for robust scalar
    regression of G.
    """
    targets_minus_base: list[float] = []
    basis_values: list[float] = []

    for segment in segments:
        samples = segment.samples

        base_prediction = samples[0].y
        basis_prediction = 0.0

        for previous, actual in zip(samples, samples[1:]):
            dt = actual.t - previous.t

            if dt <= 0:
                continue

            a = math.exp(-dt / tau_s)
            phi = input_feature(
                previous.u,
                deadzone_dac=deadzone_dac,
                exponent=exponent,
            )

            base_prediction = (
                baseline_raw
                + a * (base_prediction - baseline_raw)
            )
            basis_prediction = (
                a * basis_prediction
                + (1.0 - a) * phi
            )

            targets_minus_base.append(
                actual.y - base_prediction
            )
            basis_values.append(basis_prediction)

    return targets_minus_base, basis_values


def robust_positive_scalar_fit(
    targets: list[float],
    basis: list[float],
    *,
    huber_delta_raw: float,
    iterations: int = 20,
) -> float | None:
    if not targets or len(targets) != len(basis):
        return None

    weights = [1.0] * len(targets)
    gain = 0.0

    for _ in range(iterations):
        numerator = sum(
            weight * x * y
            for weight, x, y in zip(weights, basis, targets)
        )
        denominator = sum(
            weight * x * x
            for weight, x in zip(weights, basis)
        )

        if denominator <= 1e-18:
            return None

        new_gain = numerator / denominator

        if not math.isfinite(new_gain) or new_gain <= 0.0:
            return None

        residuals = [
            target - new_gain * x
            for target, x in zip(targets, basis)
        ]

        updated_weights = []

        for residual in residuals:
            magnitude = abs(residual)
            if magnitude <= huber_delta_raw:
                updated_weights.append(1.0)
            else:
                updated_weights.append(
                    huber_delta_raw / max(magnitude, 1e-12)
                )

        if abs(new_gain - gain) <= 1e-10 * max(1.0, new_gain):
            gain = new_gain
            break

        gain = new_gain
        weights = updated_weights

    return gain if gain > 0 else None


def simulate_segments(
    segments: list[Segment],
    *,
    tau_s: float,
    deadzone_dac: float,
    exponent: float,
    equilibrium_gain: float,
    baseline_raw: float,
) -> tuple[list[float], list[float], dict[str, dict[str, float]]]:
    actual_all: list[float] = []
    predicted_all: list[float] = []
    by_source_raw: dict[str, tuple[list[float], list[float]]] = {}

    for segment in segments:
        samples = segment.samples
        prediction = samples[0].y

        source_actual, source_predicted = by_source_raw.setdefault(
            segment.source,
            ([], []),
        )

        for previous, actual in zip(samples, samples[1:]):
            dt = actual.t - previous.t

            if dt <= 0:
                continue

            a = math.exp(-dt / tau_s)
            phi = input_feature(
                previous.u,
                deadzone_dac=deadzone_dac,
                exponent=exponent,
            )

            prediction = (
                baseline_raw
                + a * (prediction - baseline_raw)
                + equilibrium_gain * (1.0 - a) * phi
            )

            actual_all.append(actual.y)
            predicted_all.append(prediction)
            source_actual.append(actual.y)
            source_predicted.append(prediction)

    source_metrics: dict[str, dict[str, float]] = {}

    for source, (actual, predicted) in by_source_raw.items():
        source_metrics[source] = calculate_metrics(actual, predicted)

    return actual_all, predicted_all, source_metrics


def calculate_metrics(
    actual: list[float],
    predicted: list[float],
) -> dict[str, float]:
    if not actual:
        return {
            "count": 0,
            "rmse_raw": float("nan"),
            "mae_raw": float("nan"),
            "bias_raw": float("nan"),
            "max_abs_error_raw": float("nan"),
        }

    errors = [
        prediction - observation
        for observation, prediction in zip(actual, predicted)
    ]

    return {
        "count": len(errors),
        "rmse_raw": math.sqrt(
            statistics.fmean(error * error for error in errors)
        ),
        "mae_raw": statistics.fmean(abs(error) for error in errors),
        "bias_raw": statistics.fmean(errors),
        "max_abs_error_raw": max(abs(error) for error in errors),
    }


def evaluate_candidate(
    training_segments: list[Segment],
    validation_segments: list[Segment],
    *,
    tau_s: float,
    deadzone_dac: float,
    exponent: float,
    baseline_raw: float,
    huber_delta_raw: float,
) -> Candidate | None:
    targets, basis = build_linear_gain_terms(
        training_segments,
        tau_s=tau_s,
        deadzone_dac=deadzone_dac,
        exponent=exponent,
        baseline_raw=baseline_raw,
    )

    gain = robust_positive_scalar_fit(
        targets,
        basis,
        huber_delta_raw=huber_delta_raw,
    )

    if gain is None:
        return None

    train_actual, train_prediction, _ = simulate_segments(
        training_segments,
        tau_s=tau_s,
        deadzone_dac=deadzone_dac,
        exponent=exponent,
        equilibrium_gain=gain,
        baseline_raw=baseline_raw,
    )
    validation_actual, validation_prediction, _ = simulate_segments(
        validation_segments,
        tau_s=tau_s,
        deadzone_dac=deadzone_dac,
        exponent=exponent,
        equilibrium_gain=gain,
        baseline_raw=baseline_raw,
    )

    train = calculate_metrics(train_actual, train_prediction)
    validation = calculate_metrics(
        validation_actual,
        validation_prediction,
    )

    if not math.isfinite(validation["rmse_raw"]):
        return None

    return Candidate(
        tau_s=tau_s,
        deadzone_dac=deadzone_dac,
        exponent=exponent,
        equilibrium_gain=gain,
        train_rmse_raw=train["rmse_raw"],
        train_mae_raw=train["mae_raw"],
        validation_rmse_raw=validation["rmse_raw"],
        validation_mae_raw=validation["mae_raw"],
        validation_bias_raw=validation["bias_raw"],
        validation_max_abs_error_raw=validation["max_abs_error_raw"],
    )


def frange(start: float, stop: float, step: float) -> Iterable[float]:
    value = start
    while value <= stop + 1e-12:
        yield round(value, 12)
        value += step


def search_grid(
    training_segments: list[Segment],
    validation_segments: list[Segment],
    *,
    tau_values: Iterable[float],
    deadzone_values: Iterable[float],
    exponent_values: Iterable[float],
    baseline_raw: float,
    huber_delta_raw: float,
) -> Candidate:
    best: Candidate | None = None

    tau_values = list(tau_values)
    deadzone_values = list(deadzone_values)
    exponent_values = list(exponent_values)

    for deadzone in deadzone_values:
        for exponent in exponent_values:
            for tau in tau_values:
                candidate = evaluate_candidate(
                    training_segments,
                    validation_segments,
                    tau_s=tau,
                    deadzone_dac=deadzone,
                    exponent=exponent,
                    baseline_raw=baseline_raw,
                    huber_delta_raw=huber_delta_raw,
                )

                if candidate is None:
                    continue

                score = (
                    candidate.validation_rmse_raw,
                    candidate.validation_mae_raw,
                    candidate.train_rmse_raw,
                )

                if best is None:
                    best = candidate
                    best_score = score
                elif score < best_score:
                    best = candidate
                    best_score = score

    if best is None:
        raise RuntimeError("No valid dead-zone Hammerstein candidate found.")

    return best


def equilibrium_raw(
    u: float,
    candidate: Candidate,
    baseline_raw: float,
) -> float:
    return (
        baseline_raw
        + candidate.equilibrium_gain
        * input_feature(
            u,
            deadzone_dac=candidate.deadzone_dac,
            exponent=candidate.exponent,
        )
    )


def implied_dac(
    target_raw: float,
    candidate: Candidate,
    baseline_raw: float,
) -> float | None:
    delta = target_raw - baseline_raw

    if delta <= 0:
        return candidate.deadzone_dac

    if candidate.equilibrium_gain <= 0:
        return None

    effective = (
        delta / candidate.equilibrium_gain
    ) ** (1.0 / candidate.exponent)

    return candidate.deadzone_dac + effective


def build_model_json(
    candidate: Candidate,
    *,
    baseline_raw: float,
    mpc_sample_s: float,
    target_raw: float,
    training_sources: list[str],
    validation_sources: list[str],
    per_source_metrics: dict[str, dict[str, float]],
) -> dict[str, object]:
    a = math.exp(-mpc_sample_s / candidate.tau_s)
    target_dac = implied_dac(target_raw, candidate, baseline_raw)

    equilibrium_table = {
        str(dac): equilibrium_raw(dac, candidate, baseline_raw)
        for dac in (9500, 10500, 11000, 11500, 11700, 12000, 12300, 13000, 14000)
    }

    return {
        "model_type": "deadzone_hammerstein_first_order",
        "continuous_time": {
            "equation": (
                "dy/dt = -(y-y0)/tau + "
                "(G/tau)*max(0,u-u_dead)^p"
            ),
            "tau_s": candidate.tau_s,
            "baseline_raw_y0": baseline_raw,
            "deadzone_DAC": candidate.deadzone_dac,
            "input_exponent_p": candidate.exponent,
            "equilibrium_gain_G_raw_per_DAC_power_p": (
                candidate.equilibrium_gain
            ),
            "equilibrium_equation": (
                "y_eq(u)=y0+G*max(0,u-u_dead)^p"
            ),
        },
        "discrete_time": {
            "sample_time_s": mpc_sample_s,
            "a": a,
            "equation": (
                "y[k+1]=y0+a*(y[k]-y0)+"
                "G*(1-a)*max(0,u[k]-u_dead)^p"
            ),
        },
        "target_operating_point": {
            "target_raw": target_raw,
            "implied_equilibrium_DAC": target_dac,
        },
        "trajectory_metrics": {
            "train_rmse_raw": candidate.train_rmse_raw,
            "train_mae_raw": candidate.train_mae_raw,
            "validation_rmse_raw": candidate.validation_rmse_raw,
            "validation_mae_raw": candidate.validation_mae_raw,
            "validation_bias_raw": candidate.validation_bias_raw,
            "validation_max_abs_error_raw": (
                candidate.validation_max_abs_error_raw
            ),
        },
        "equilibrium_table_raw": equilibrium_table,
        "training_sources": training_sources,
        "validation_sources": validation_sources,
        "per_source_rollout_metrics": per_source_metrics,
        "physical_constraints": {
            "tau_positive": candidate.tau_s > 0,
            "deadzone_nonnegative": candidate.deadzone_dac >= 0,
            "input_exponent_positive": candidate.exponent > 0,
            "equilibrium_gain_positive": candidate.equilibrium_gain > 0,
            "monotone_input_to_equilibrium": True,
            "stable_state_dynamics": 0 < a < 1,
        },
        "caution": (
            "Candidate nonlinear model identified from preserved laboratory "
            "trajectories. It must pass offline MPC robustness tests before "
            "real commissioning."
        ),
    }


def write_report(
    path: Path,
    model: dict[str, object],
) -> None:
    ct = model["continuous_time"]
    metrics = model["trajectory_metrics"]
    target = model["target_operating_point"]

    lines = [
        "# Dead-zone Hammerstein Model Identification",
        "",
        "## Purpose",
        "",
        "Trajectory-level nonlinear identification using preserved laboratory "
        "data. This model explicitly represents the experimentally observed "
        "pump dead-zone/nonlinearity.",
        "",
        "## Selected model",
        "",
        f"- tau: {ct['tau_s']:.6f} s",
        f"- sensor/raw baseline y0: {ct['baseline_raw_y0']:.3f} raw",
        f"- pump dead-zone: {ct['deadzone_DAC']:.3f} DAC",
        f"- input exponent p: {ct['input_exponent_p']:.6f}",
        (
            "- equilibrium gain G: "
            f"{ct['equilibrium_gain_G_raw_per_DAC_power_p']:.12g}"
        ),
        "",
        "```text",
        ct["equilibrium_equation"],
        "```",
        "",
        "## Validation",
        "",
        f"- training rollout RMSE: {metrics['train_rmse_raw']:.3f} raw",
        f"- validation rollout RMSE: {metrics['validation_rmse_raw']:.3f} raw",
        f"- validation rollout MAE: {metrics['validation_mae_raw']:.3f} raw",
        f"- validation bias: {metrics['validation_bias_raw']:.3f} raw",
        (
            "- validation maximum absolute error: "
            f"{metrics['validation_max_abs_error_raw']:.3f} raw"
        ),
        "",
        "## Target implication",
        "",
        f"- target: {target['target_raw']:.3f} raw",
        (
            "- implied equilibrium DAC: "
            f"{target['implied_equilibrium_DAC']}"
        ),
        "",
        "## Decision",
        "",
        "This file identifies a candidate model only. Real MPC remains "
        "unauthorized until offline robustness and constraint tests pass.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit a stable monotone first-order Hammerstein model with an "
            "explicit pump dead-zone from preserved real trajectories. "
            "Offline only."
        )
    )

    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--validation-source-pattern",
        default="steady-calibration-20260808-103827",
        help=(
            "substring identifying source file(s) reserved for validation; "
            "default is the independent 12000-DAC 20-s plateau"
        ),
    )
    parser.add_argument("--baseline-raw", type=float, default=298.0)
    parser.add_argument("--minimum-raw", type=float, default=150.0)
    parser.add_argument("--maximum-raw", type=float, default=1250.0)
    parser.add_argument("--maximum-gap-s", type=float, default=0.6)
    parser.add_argument("--minimum-segment-samples", type=int, default=15)
    parser.add_argument("--huber-delta-raw", type=float, default=60.0)
    parser.add_argument("--mpc-sample-s", type=float, default=0.1)
    parser.add_argument("--target-raw", type=float, default=450.0)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("DEAD-ZONE HAMMERSTEIN MODEL IDENTIFICATION")
    print("==========================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print()

    sources = discover_sources(args.data_root)

    all_segments: list[Segment] = []
    source_counts: dict[str, int] = {}

    for source in sources:
        samples = read_active_samples(
            source,
            minimum_raw=args.minimum_raw,
            maximum_raw=args.maximum_raw,
        )
        segments = make_segments(
            source,
            samples,
            maximum_gap_s=args.maximum_gap_s,
            minimum_segment_samples=args.minimum_segment_samples,
        )
        all_segments.extend(segments)
        source_counts[str(source)] = sum(
            len(segment.samples) for segment in segments
        )

    validation_segments = [
        segment
        for segment in all_segments
        if args.validation_source_pattern.lower() in segment.source.lower()
    ]
    training_segments = [
        segment
        for segment in all_segments
        if args.validation_source_pattern.lower() not in segment.source.lower()
    ]

    if not training_segments:
        raise SystemExit("No training segments found.")

    if not validation_segments:
        raise SystemExit(
            "No validation segment matched "
            f"{args.validation_source_pattern!r}."
        )

    print(f"Source files discovered: {len(sources)}")
    print(f"Training segments: {len(training_segments)}")
    print(f"Validation segments: {len(validation_segments)}")
    print(
        "Training samples: "
        f"{sum(len(segment.samples) for segment in training_segments)}"
    )
    print(
        "Validation samples: "
        f"{sum(len(segment.samples) for segment in validation_segments)}"
    )
    print()

    print("COARSE SEARCH")
    print("-------------")

    coarse = search_grid(
        training_segments,
        validation_segments,
        tau_values=frange(2.0, 30.0, 0.5),
        deadzone_values=frange(9500.0, 11700.0, 100.0),
        exponent_values=frange(1.0, 3.0, 0.25),
        baseline_raw=args.baseline_raw,
        huber_delta_raw=args.huber_delta_raw,
    )

    print(f"tau: {coarse.tau_s:.3f} s")
    print(f"deadzone: {coarse.deadzone_dac:.1f} DAC")
    print(f"exponent: {coarse.exponent:.3f}")
    print(f"validation RMSE: {coarse.validation_rmse_raw:.3f} raw")
    print()

    print("REFINED SEARCH")
    print("--------------")

    refined = search_grid(
        training_segments,
        validation_segments,
        tau_values=frange(
            max(1.0, coarse.tau_s - 2.0),
            coarse.tau_s + 2.0,
            0.1,
        ),
        deadzone_values=frange(
            max(9000.0, coarse.deadzone_dac - 150.0),
            min(11900.0, coarse.deadzone_dac + 150.0),
            25.0,
        ),
        exponent_values=frange(
            max(0.5, coarse.exponent - 0.30),
            min(3.5, coarse.exponent + 0.30),
            0.05,
        ),
        baseline_raw=args.baseline_raw,
        huber_delta_raw=args.huber_delta_raw,
    )

    all_actual, all_prediction, per_source_metrics = simulate_segments(
        all_segments,
        tau_s=refined.tau_s,
        deadzone_dac=refined.deadzone_dac,
        exponent=refined.exponent,
        equilibrium_gain=refined.equilibrium_gain,
        baseline_raw=args.baseline_raw,
    )

    training_sources = sorted({segment.source for segment in training_segments})
    validation_sources = sorted({segment.source for segment in validation_segments})

    model = build_model_json(
        refined,
        baseline_raw=args.baseline_raw,
        mpc_sample_s=args.mpc_sample_s,
        target_raw=args.target_raw,
        training_sources=training_sources,
        validation_sources=validation_sources,
        per_source_metrics=per_source_metrics,
    )

    args.output_root.mkdir(parents=True, exist_ok=True)

    model_path = args.output_root / "selected-nonlinear-model.json"
    report_path = args.output_root / "identification-report.md"

    model_path.write_text(
        json.dumps(model, indent=2),
        encoding="utf-8",
    )
    write_report(report_path, model)

    ct = model["continuous_time"]
    metrics = model["trajectory_metrics"]
    target = model["target_operating_point"]

    print()
    print("SELECTED NONLINEAR MODEL")
    print("------------------------")
    print(f"tau_s: {ct['tau_s']:.6f}")
    print(f"baseline raw: {ct['baseline_raw_y0']:.3f}")
    print(f"deadzone DAC: {ct['deadzone_DAC']:.3f}")
    print(f"input exponent: {ct['input_exponent_p']:.6f}")
    print(
        "equilibrium gain: "
        f"{ct['equilibrium_gain_G_raw_per_DAC_power_p']:.12g}"
    )
    print()
    print(
        "training rollout RMSE raw: "
        f"{metrics['train_rmse_raw']:.6f}"
    )
    print(
        "validation rollout RMSE raw: "
        f"{metrics['validation_rmse_raw']:.6f}"
    )
    print(
        "validation rollout MAE raw: "
        f"{metrics['validation_mae_raw']:.6f}"
    )
    print(
        "validation bias raw: "
        f"{metrics['validation_bias_raw']:.6f}"
    )
    print(
        "validation max abs error raw: "
        f"{metrics['validation_max_abs_error_raw']:.6f}"
    )
    print()
    print(
        "implied equilibrium DAC at target: "
        f"{target['implied_equilibrium_DAC']}"
    )
    print()
    print(f"Model: {model_path}")
    print(f"Report: {report_path}")
    print()
    print("PHYSICAL DEAD-ZONE REPRESENTED: YES")
    print("POSITIVE MONOTONE INPUT EFFECT: YES")
    print("STABLE STATE DYNAMICS: YES")
    print("REAL MPC AUTHORIZED: NO")
    print("NEXT: inspect independent trajectory validation")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
