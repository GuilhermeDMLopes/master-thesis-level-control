from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "sample" / "mpc-v4-target17000-20260829"
ACTIVE = EVIDENCE / "first-active-monitor.csv"
PRE = EVIDENCE / "predeployment-zero-output-monitor.csv"
POST = EVIDENCE / "postshutdown-zero-output-monitor.csv"
METRICS = EVIDENCE / "metrics.json"
FIGURES = ROOT / "docs" / "figures" / "mpc-v4-target17000"
TARGET_RAW = 17000.0


def normalize_svg(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    payload = "\n".join(line.rstrip() for line in lines) + "\n"
    path.write_bytes(payload.encode("utf-8"))


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def calculate_metrics() -> dict[str, object]:
    rows = load(ACTIVE)
    active = [row for row in rows if float(row["active_elapsed_s"]) >= 0.0]
    if not active:
        raise RuntimeError("No active samples found")

    t = [float(row["active_elapsed_s"]) for row in active]
    median = [float(row["median9_raw"]) for row in active]
    instant = [float(row["plc_nivel"]) for row in active]
    applied_dac = [float(row["plc_applied_dac"]) for row in active]
    errors = [TARGET_RAW - value for value in median]

    def first_reach(level: float) -> float | None:
        return next(
            (time_s for time_s, value in zip(t, median) if value >= level),
            None,
        )

    def settling_time(fraction: float) -> float | None:
        low = TARGET_RAW * (1.0 - fraction)
        high = TARGET_RAW * (1.0 + fraction)
        for index, time_s in enumerate(t):
            if all(low <= value <= high for value in median[index:]):
                return time_s
        return None

    tail30_indices = [index for index, value in enumerate(t) if value >= t[-1] - 30.0]
    tail20_indices = [index for index, value in enumerate(t) if value >= t[-1] - 20.0]
    tail30 = [median[index] for index in tail30_indices]
    tail20 = [median[index] for index in tail20_indices]
    tail30_dac = [applied_dac[index] for index in tail30_indices]
    tail30_errors = [TARGET_RAW - value for value in tail30]

    pre = load(PRE)
    post = load(POST)

    def all_zero_healthy(samples: list[dict[str, str]]) -> bool:
        return all(
            row["gw_enable"] == "False"
            and float(row["gw_dac"]) == 0.0
            and row["plc_applied_enable"] == "False"
            and float(row["plc_applied_dac"]) == 0.0
            and row["gw_watchdog_healthy"] == "True"
            and row["plc_watchdog_healthy"] == "True"
            for row in samples
        )

    first10 = first_reach(TARGET_RAW * 0.1)
    first90 = first_reach(TARGET_RAW * 0.9)
    maximum_median = max(median)

    return {
        "status": "validated_real_plant_15cm",
        "experiment_date": "2026-08-29",
        "target_raw": TARGET_RAW,
        "physical_height_cm": 15.0,
        "physical_observation": "The level reached 15 cm and stabilized.",
        "shutdown_reason": "ACTIVE_WINDOW_COMPLETE",
        "samples_total": len(rows),
        "samples_active": len(active),
        "active_duration_s": t[-1] - t[0],
        "effective_sample_period_median_s": statistics.median(
            [b - a for a, b in zip(t, t[1:])]
        ),
        "initial_median_raw": median[0],
        "maximum_instant_raw": max(instant),
        "maximum_median_raw": maximum_median,
        "overshoot_raw": max(0.0, maximum_median - TARGET_RAW),
        "overshoot_percent": max(0.0, maximum_median - TARGET_RAW)
        / TARGET_RAW
        * 100.0,
        "first_10_percent_s": first10,
        "first_50_percent_s": first_reach(TARGET_RAW * 0.5),
        "first_90_percent_s": first90,
        "first_target_s": first_reach(TARGET_RAW),
        "rise_time_10_to_90_s": first90 - first10,
        "settling_time_5_percent_s": settling_time(0.05),
        "settling_time_2_percent_s": settling_time(0.02),
        "iae_raw_s": sum(
            abs((left + right) / 2.0) * (end - start)
            for start, end, left, right in zip(t, t[1:], errors, errors[1:])
        ),
        "rmse_raw_full": math.sqrt(mean([value * value for value in errors])),
        "mae_raw_full": mean([abs(value) for value in errors]),
        "tail20_mean_raw": mean(tail20),
        "tail30_mean_raw": mean(tail30),
        "tail30_median_raw": statistics.median(tail30),
        "tail30_std_raw": std(tail30),
        "tail30_min_raw": min(tail30),
        "tail30_max_raw": max(tail30),
        "tail30_mean_error_raw": mean(tail30_errors),
        "tail30_mae_raw": mean([abs(value) for value in tail30_errors]),
        "tail30_rmse_raw": math.sqrt(
            mean([value * value for value in tail30_errors])
        ),
        "maximum_applied_dac": max(applied_dac),
        "tail30_mean_applied_dac": mean(tail30_dac),
        "tail30_min_applied_dac": min(tail30_dac),
        "tail30_max_applied_dac": max(tail30_dac),
        "applied_dac_total_variation": sum(
            abs(right - left)
            for left, right in zip(applied_dac, applied_dac[1:])
        ),
        "watchdog_healthy_all_active": all(
            row["gw_watchdog_healthy"] == "True"
            and row["plc_watchdog_healthy"] == "True"
            and row["plc_watchdog_tripped"] == "False"
            for row in active
        ),
        "predeployment_samples": len(pre),
        "predeployment_zero_all_samples": all_zero_healthy(pre),
        "postshutdown_samples": len(post),
        "postshutdown_zero_all_samples": all_zero_healthy(post),
    }


def generate_figures() -> None:
    rows = [
        row
        for row in load(ACTIVE)
        if float(row["active_elapsed_s"]) >= 0.0
    ]
    t = [float(row["active_elapsed_s"]) for row in rows]
    instant = [float(row["plc_nivel"]) for row in rows]
    median = [float(row["median9_raw"]) for row in rows]
    requested = [float(row["gw_dac"]) for row in rows]
    applied = [float(row["plc_applied_dac"]) for row in rows]
    error = [TARGET_RAW - value for value in median]

    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "svg.hashsalt": "mpc-v4-target17000",
        }
    )

    figure, axis = plt.subplots(figsize=(9.0, 4.8), constrained_layout=True)
    axis.plot(t, instant, color="#9AA5B1", linewidth=0.8, alpha=0.65, label="Raw level")
    axis.plot(t, median, color="#1261A0", linewidth=2.0, label="Median-9 level")
    axis.axhline(TARGET_RAW, color="#C73E1D", linestyle="--", linewidth=1.5, label="Target 17000 raw (15 cm)")
    axis.axhspan(TARGET_RAW * 0.95, TARGET_RAW * 1.05, color="#2A9D8F", alpha=0.10, label="+/-5% band")
    axis.set(xlabel="Active time (s)", ylabel="Level (raw)", xlim=(0, 180), title="Real-plant MPC V4 level response")
    axis.legend(loc="lower right")
    for suffix in ("png", "svg"):
        figure.savefig(FIGURES / f"mpc-v4-target17000-level.{suffix}", dpi=180, metadata={"Date": None})
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9.0, 4.2), constrained_layout=True)
    axis.plot(t, requested, color="#E76F51", linewidth=1.2, label="Gateway command")
    axis.plot(t, applied, color="#264653", linewidth=1.8, label="Applied DAC")
    axis.set(xlabel="Active time (s)", ylabel="DAC", xlim=(0, 180), ylim=(0, 16800), title="Real-plant MPC V4 control effort")
    axis.legend(loc="lower right")
    for suffix in ("png", "svg"):
        figure.savefig(FIGURES / f"mpc-v4-target17000-dac.{suffix}", dpi=180, metadata={"Date": None})
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9.0, 4.2), constrained_layout=True)
    axis.plot(t, error, color="#6A4C93", linewidth=1.8)
    axis.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0)
    axis.set(xlabel="Active time (s)", ylabel="Tracking error (raw)", xlim=(0, 180), title="Real-plant MPC V4 tracking error")
    for suffix in ("png", "svg"):
        figure.savefig(FIGURES / f"mpc-v4-target17000-error.{suffix}", dpi=180, metadata={"Date": None})
    plt.close(figure)

    for svg_path in sorted(FIGURES.glob("*.svg")):
        normalize_svg(svg_path)


def main() -> int:
    metrics = calculate_metrics()
    METRICS.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generate_figures()
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"Metrics: {METRICS}")
    print(f"Figures: {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
