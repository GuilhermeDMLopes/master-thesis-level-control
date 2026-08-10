from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EXPECTED_SHA256 = (
    "197D0F0113564EACC40D16325CF1760008C595CE815300DA8BE5841CAB060E07"
)

DEFAULT_INPUT = Path("data/sample/real-raw-pi-v1-monitor.csv")
DEFAULT_OUTPUT = Path("results/mpc/pi-baseline-identification")


@dataclass(frozen=True)
class Sample:
    t: float
    y: float
    u: float


@dataclass(frozen=True)
class Model:
    na: int
    nb: int
    delay: int
    coefficients: tuple[float, ...]
    y_offset: float
    u_offset: float
    sample_time_s: float
    train_rmse: float
    validation_one_step_rmse: float
    validation_free_run_rmse: float
    validation_fit_percent: float
    validation_bias: float
    validation_max_abs_error: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def median(values: Iterable[float]) -> float:
    return float(statistics.median(list(values)))


def load_auto_samples(path: Path) -> list[Sample]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if reader.fieldnames is None:
            raise RuntimeError("CSV has no header.")

        required = {
            "elapsed_s",
            "phase",
            "rolling_median_level",
            "applied_enable",
            "applied_dac",
        }
        missing = required.difference(reader.fieldnames)
        if missing:
            raise RuntimeError(
                "Missing columns: " + ", ".join(sorted(missing))
            )

        samples: list[Sample] = []
        for row in reader:
            if row["phase"].strip() != "AUTO_ACTIVE":
                continue
            if not as_bool(row["applied_enable"]):
                continue

            samples.append(
                Sample(
                    t=float(row["elapsed_s"]),
                    y=float(row["rolling_median_level"]),
                    u=float(row["applied_dac"]),
                )
            )

    if len(samples) < 80:
        raise RuntimeError(
            f"Too few AUTO_ACTIVE samples for identification: {len(samples)}"
        )

    return samples


def sample_interval_summary(samples: list[Sample]) -> dict[str, float]:
    intervals = [
        b.t - a.t
        for a, b in zip(samples, samples[1:])
        if b.t > a.t
    ]
    if not intervals:
        raise RuntimeError("No positive sample intervals.")

    return {
        "minimum": min(intervals),
        "maximum": max(intervals),
        "median": statistics.median(intervals),
        "mean": statistics.fmean(intervals),
    }


def interpolate(samples: list[Sample], ts: float) -> list[Sample]:
    start = samples[0].t
    end = samples[-1].t

    result: list[Sample] = []
    index = 0
    t = start

    while t <= end + 1e-9:
        while (
            index + 1 < len(samples)
            and samples[index + 1].t < t
        ):
            index += 1

        if index + 1 >= len(samples):
            a = b = samples[-1]
        else:
            a = samples[index]
            b = samples[index + 1]

        if b.t <= a.t or t <= a.t:
            fraction = 0.0
        elif t >= b.t:
            fraction = 1.0
        else:
            fraction = (t - a.t) / (b.t - a.t)

        y = a.y + fraction * (b.y - a.y)
        u = a.u + fraction * (b.u - a.u)

        result.append(Sample(t=t, y=y, u=u))
        t += ts

    return result


def solve_linear_system(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float]:
    n = len(vector)
    augmented = [
        [float(value) for value in row] + [float(vector[i])]
        for i, row in enumerate(matrix)
    ]

    for column in range(n):
        pivot = max(
            range(column, n),
            key=lambda row: abs(augmented[row][column]),
        )

        if abs(augmented[pivot][column]) < 1e-12:
            raise RuntimeError("Singular normal-equation matrix.")

        if pivot != column:
            augmented[column], augmented[pivot] = (
                augmented[pivot],
                augmented[column],
            )

        divisor = augmented[column][column]
        augmented[column] = [
            value / divisor
            for value in augmented[column]
        ]

        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value in zip(
                    augmented[row],
                    augmented[column],
                )
            ]

    return [augmented[i][-1] for i in range(n)]


def ridge_fit(
    x_rows: list[list[float]],
    targets: list[float],
    ridge: float,
) -> list[float]:
    width = len(x_rows[0])

    xtx = [
        [0.0 for _ in range(width)]
        for _ in range(width)
    ]
    xty = [0.0 for _ in range(width)]

    for row, target in zip(x_rows, targets):
        for i in range(width):
            xty[i] += row[i] * target
            for j in range(width):
                xtx[i][j] += row[i] * row[j]

    scale = max(
        1.0,
        sum(xtx[i][i] for i in range(width)) / width,
    )
    regularization = ridge * scale

    for i in range(width):
        xtx[i][i] += regularization

    return solve_linear_system(xtx, xty)


def feature_row(
    y: list[float],
    u: list[float],
    k: int,
    *,
    na: int,
    nb: int,
    delay: int,
) -> list[float]:
    row = [1.0]

    for lag in range(1, na + 1):
        row.append(y[k - lag])

    first_input_index = k - delay
    for lag in range(nb):
        row.append(u[first_input_index - lag])

    return row


def first_valid_index(na: int, nb: int, delay: int) -> int:
    return max(na, delay + nb - 1)


def rmse(actual: list[float], predicted: list[float]) -> float:
    if not actual:
        return float("inf")
    return math.sqrt(
        statistics.fmean(
            (a - p) ** 2
            for a, p in zip(actual, predicted)
        )
    )


def mean_error(actual: list[float], predicted: list[float]) -> float:
    return statistics.fmean(
        p - a
        for a, p in zip(actual, predicted)
    )


def one_step_predict(
    y: list[float],
    u: list[float],
    coefficients: list[float],
    *,
    na: int,
    nb: int,
    delay: int,
    start: int,
    end: int,
) -> tuple[list[float], list[float]]:
    actual: list[float] = []
    predicted: list[float] = []

    for k in range(start, end):
        row = feature_row(
            y,
            u,
            k,
            na=na,
            nb=nb,
            delay=delay,
        )
        prediction = sum(
            coefficient * value
            for coefficient, value in zip(coefficients, row)
        )
        actual.append(y[k])
        predicted.append(prediction)

    return actual, predicted


def free_run_predict(
    y: list[float],
    u: list[float],
    coefficients: list[float],
    *,
    na: int,
    nb: int,
    delay: int,
    start: int,
    end: int,
) -> tuple[list[float], list[float]]:
    simulated = list(y[:start])
    actual: list[float] = []
    predicted: list[float] = []

    for k in range(start, end):
        row = [1.0]

        for lag in range(1, na + 1):
            index = k - lag
            if index < len(simulated):
                row.append(simulated[index])
            else:
                row.append(y[index])

        first_input_index = k - delay
        for lag in range(nb):
            row.append(u[first_input_index - lag])

        prediction = sum(
            coefficient * value
            for coefficient, value in zip(coefficients, row)
        )

        if not math.isfinite(prediction) or abs(prediction) > 10000:
            return [], []

        simulated.append(prediction)
        actual.append(y[k])
        predicted.append(prediction)

    return actual, predicted


def identify_candidate(
    samples: list[Sample],
    *,
    train_end: int,
    na: int,
    nb: int,
    delay: int,
    ridge: float,
    sample_time_s: float,
) -> Model | None:
    y_raw = [sample.y for sample in samples]
    u_raw = [sample.u for sample in samples]

    y_offset = statistics.fmean(y_raw[:train_end])
    u_offset = statistics.fmean(u_raw[:train_end])

    y = [value - y_offset for value in y_raw]
    u = [value - u_offset for value in u_raw]

    first = first_valid_index(na, nb, delay)

    if first >= train_end - 10:
        return None

    x_rows: list[list[float]] = []
    targets: list[float] = []

    for k in range(first, train_end):
        x_rows.append(
            feature_row(
                y,
                u,
                k,
                na=na,
                nb=nb,
                delay=delay,
            )
        )
        targets.append(y[k])

    try:
        coefficients = ridge_fit(x_rows, targets, ridge)
    except RuntimeError:
        return None

    train_actual, train_pred = one_step_predict(
        y,
        u,
        coefficients,
        na=na,
        nb=nb,
        delay=delay,
        start=first,
        end=train_end,
    )

    validation_start = max(train_end, first)

    val_actual, val_one = one_step_predict(
        y,
        u,
        coefficients,
        na=na,
        nb=nb,
        delay=delay,
        start=validation_start,
        end=len(samples),
    )

    free_actual, val_free = free_run_predict(
        y,
        u,
        coefficients,
        na=na,
        nb=nb,
        delay=delay,
        start=validation_start,
        end=len(samples),
    )

    if not free_actual:
        return None

    train_error = rmse(train_actual, train_pred)
    one_error = rmse(val_actual, val_one)
    free_error = rmse(free_actual, val_free)

    val_std = statistics.pstdev(val_actual)
    fit_percent = (
        100.0 * (1.0 - free_error / val_std)
        if val_std > 1e-9
        else float("-inf")
    )

    bias = mean_error(free_actual, val_free)
    max_abs = max(
        abs(a - p)
        for a, p in zip(free_actual, val_free)
    )

    return Model(
        na=na,
        nb=nb,
        delay=delay,
        coefficients=tuple(coefficients),
        y_offset=y_offset,
        u_offset=u_offset,
        sample_time_s=sample_time_s,
        train_rmse=train_error,
        validation_one_step_rmse=one_error,
        validation_free_run_rmse=free_error,
        validation_fit_percent=fit_percent,
        validation_bias=bias,
        validation_max_abs_error=max_abs,
    )


def model_to_dict(model: Model) -> dict[str, object]:
    coefficient_index = 1
    a = list(
        model.coefficients[
            coefficient_index : coefficient_index + model.na
        ]
    )
    coefficient_index += model.na
    b = list(
        model.coefficients[
            coefficient_index : coefficient_index + model.nb
        ]
    )

    return {
        "model_type": "empirical_closed_loop_arx",
        "sample_time_s": model.sample_time_s,
        "na": model.na,
        "nb": model.nb,
        "input_delay_samples": model.delay,
        "input_delay_s": model.delay * model.sample_time_s,
        "intercept_deviation_form": model.coefficients[0],
        "a": a,
        "b": b,
        "y_offset_raw": model.y_offset,
        "u_offset_dac": model.u_offset,
        "metrics": {
            "train_one_step_rmse_raw": model.train_rmse,
            "validation_one_step_rmse_raw": (
                model.validation_one_step_rmse
            ),
            "validation_free_run_rmse_raw": (
                model.validation_free_run_rmse
            ),
            "validation_free_run_fit_percent": (
                model.validation_fit_percent
            ),
            "validation_free_run_bias_raw": (
                model.validation_bias
            ),
            "validation_max_abs_error_raw": (
                model.validation_max_abs_error
            ),
        },
        "equation": (
            "dy[k] = c + sum(a_i*dy[k-i]) + "
            "sum(b_j*du[k-delay-j]); "
            "y = dy + y_offset, u = du + u_offset"
        ),
        "caution": (
            "Identified from closed-loop PI data. Use as an initial "
            "MPC model only after independent offline/real validation."
        ),
    }


def write_report(
    path: Path,
    *,
    source: Path,
    source_hash: str,
    original_count: int,
    resampled_count: int,
    interval_summary: dict[str, float],
    sample_time_s: float,
    train_end: int,
    models: list[Model],
) -> None:
    best = models[0]
    best_dict = model_to_dict(best)

    lines = [
        "# PI Baseline MPC Model Identification",
        "",
        "## Scope",
        "",
        "This analysis is entirely offline.",
        "It uses only the validated `AUTO_ACTIVE` portion of the "
        "preserved real PI baseline.",
        "",
        "**Important:** this is a closed-loop empirical identification. "
        "It is an initial MPC model candidate, not yet an independently "
        "validated plant model.",
        "",
        "## Source",
        "",
        f"- CSV: `{source.as_posix()}`",
        f"- SHA-256: `{source_hash}`",
        f"- Original AUTO_ACTIVE rows: {original_count}",
        f"- Uniformly resampled rows: {resampled_count}",
        f"- Identification sample time: {sample_time_s:.6f} s",
        (
            "- Original interval median: "
            f"{interval_summary['median']:.6f} s"
        ),
        f"- Training rows: {train_end}",
        f"- Validation rows: {resampled_count - train_end}",
        "",
        "## Selected Model",
        "",
        f"- AR order (`na`): {best.na}",
        f"- Input order (`nb`): {best.nb}",
        f"- Input delay: {best.delay} samples "
        f"({best.delay * sample_time_s:.3f} s)",
        f"- Output offset: {best.y_offset:.3f} raw",
        f"- Input offset: {best.u_offset:.3f} DAC",
        (
            "- Validation free-run RMSE: "
            f"{best.validation_free_run_rmse:.3f} raw"
        ),
        (
            "- Validation free-run fit: "
            f"{best.validation_fit_percent:.2f} %"
        ),
        (
            "- Validation free-run bias: "
            f"{best.validation_bias:.3f} raw"
        ),
        (
            "- Validation maximum absolute error: "
            f"{best.validation_max_abs_error:.3f} raw"
        ),
        "",
        "### Difference-equation coefficients",
        "",
        "```json",
        json.dumps(best_dict, indent=2),
        "```",
        "",
        "## Candidate Leaderboard",
        "",
        "| Rank | na | nb | delay | delay s | train RMSE | "
        "val 1-step RMSE | val free-run RMSE | val fit % |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for rank, model in enumerate(models[:12], start=1):
        lines.append(
            f"| {rank} | {model.na} | {model.nb} | {model.delay} | "
            f"{model.delay * sample_time_s:.3f} | "
            f"{model.train_rmse:.3f} | "
            f"{model.validation_one_step_rmse:.3f} | "
            f"{model.validation_free_run_rmse:.3f} | "
            f"{model.validation_fit_percent:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Decision Rule",
            "",
            "The selected model minimizes validation free-run RMSE. "
            "A useful numerical fit does not by itself authorize the "
            "real MPC. The next stage must test the model offline and "
            "compare its predictions against data not used for fitting.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Identify and validate low-order ARX candidates from the "
            "preserved real PI baseline. Offline only."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--expected-sha256",
        default=EXPECTED_SHA256,
    )
    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.65,
    )
    parser.add_argument(
        "--maximum-delay-s",
        type=float,
        default=3.0,
    )
    parser.add_argument(
        "--ridge",
        type=float,
        default=1e-8,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not 0.5 <= args.train_fraction <= 0.85:
        raise SystemExit("train-fraction must be between 0.5 and 0.85")

    source_hash = sha256(args.input)

    if (
        args.expected_sha256
        and source_hash.upper() != args.expected_sha256.upper()
    ):
        raise SystemExit(
            "Baseline SHA-256 mismatch. "
            f"Expected {args.expected_sha256}, got {source_hash}."
        )

    original = load_auto_samples(args.input)
    intervals = sample_interval_summary(original)
    ts = float(intervals["median"])

    uniform = interpolate(original, ts)

    train_end = int(len(uniform) * args.train_fraction)
    train_end = max(40, min(train_end, len(uniform) - 30))

    maximum_delay = max(
        0,
        int(round(args.maximum_delay_s / ts)),
    )

    models: list[Model] = []

    for na in range(1, 4):
        for nb in range(1, 4):
            for delay in range(0, maximum_delay + 1):
                model = identify_candidate(
                    uniform,
                    train_end=train_end,
                    na=na,
                    nb=nb,
                    delay=delay,
                    ridge=args.ridge,
                    sample_time_s=ts,
                )

                if model is None:
                    continue

                if not math.isfinite(
                    model.validation_free_run_rmse
                ):
                    continue

                models.append(model)

    if not models:
        raise SystemExit("No valid candidate model was identified.")

    models.sort(
        key=lambda model: (
            model.validation_free_run_rmse,
            model.validation_one_step_rmse,
            model.na + model.nb,
            model.delay,
        )
    )

    args.output_root.mkdir(parents=True, exist_ok=True)

    best_path = args.output_root / "selected-model.json"
    candidates_path = args.output_root / "candidate-models.json"
    report_path = args.output_root / "identification-report.md"

    best_path.write_text(
        json.dumps(
            model_to_dict(models[0]),
            indent=2,
        ),
        encoding="utf-8",
    )

    candidates_path.write_text(
        json.dumps(
            [
                model_to_dict(model)
                for model in models[:30]
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    write_report(
        report_path,
        source=args.input,
        source_hash=source_hash,
        original_count=len(original),
        resampled_count=len(uniform),
        interval_summary=intervals,
        sample_time_s=ts,
        train_end=train_end,
        models=models,
    )

    best = models[0]

    print("PI BASELINE MPC MODEL IDENTIFICATION")
    print("====================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"Source SHA256: {source_hash}")
    print(f"AUTO_ACTIVE rows: {len(original)}")
    print(f"Resampled rows: {len(uniform)}")
    print(f"Sample time: {ts:.6f} s")
    print(f"Training rows: {train_end}")
    print(f"Validation rows: {len(uniform) - train_end}")
    print()
    print("SELECTED MODEL")
    print("--------------")
    print(f"na: {best.na}")
    print(f"nb: {best.nb}")
    print(f"delay samples: {best.delay}")
    print(
        f"delay seconds: "
        f"{best.delay * best.sample_time_s:.6f}"
    )
    print(f"y offset raw: {best.y_offset:.6f}")
    print(f"u offset DAC: {best.u_offset:.6f}")
    print(
        "validation one-step RMSE raw: "
        f"{best.validation_one_step_rmse:.6f}"
    )
    print(
        "validation free-run RMSE raw: "
        f"{best.validation_free_run_rmse:.6f}"
    )
    print(
        "validation free-run fit percent: "
        f"{best.validation_fit_percent:.3f}"
    )
    print(
        "validation max abs error raw: "
        f"{best.validation_max_abs_error:.6f}"
    )
    print()
    print(f"Selected model: {best_path}")
    print(f"Candidate models: {candidates_path}")
    print(f"Report: {report_path}")
    print()
    print("REAL MPC AUTHORIZED: NO")
    print("NEXT: independent offline model validation")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
