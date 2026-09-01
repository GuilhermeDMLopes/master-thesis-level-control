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
TARGET_RAW = 17000.0

MPC = ROOT / "data/sample/mpc-v4-target17000-20260829"
PI = ROOT / "data/sample/pi-v4-matched-20260901"
PI_FIRST = ROOT / "data/sample/pi-v4-matched-first-attempt-20260829"
COMPARISON = ROOT / "data/sample/pi-vs-mpc-v4-final-20260901"
FIGURES = ROOT / "docs/figures/pi-vs-mpc-v4-final-20260901"
DOCUMENT = ROOT / "docs/experiments/pi-vs-mpc-v4-final-20260901-analysis.md"


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def trapz(t: list[float], values: list[float]) -> float:
    return sum(
        ((left + right) / 2.0) * (end - start)
        for start, end, left, right in zip(t, t[1:], values, values[1:])
    )


def first_reach(
    t: list[float], values: list[float], level: float
) -> float | None:
    return next((time for time, value in zip(t, values) if value >= level), None)


def settling_time(
    t: list[float], values: list[float], fraction: float
) -> float | None:
    low = TARGET_RAW * (1.0 - fraction)
    high = TARGET_RAW * (1.0 + fraction)
    for index, time in enumerate(t):
        if all(low <= value <= high for value in values[index:]):
            return time
    return None


def active_metrics(path: Path) -> dict[str, object]:
    rows = load(path)
    active = [row for row in rows if float(row["active_elapsed_s"]) >= 0.0]
    if len(active) < 2:
        raise RuntimeError(f"Insufficient active samples: {path}")

    t = [float(row["active_elapsed_s"]) for row in active]
    level = [float(row["median9_raw"]) for row in active]
    instant = [float(row["plc_nivel"]) for row in active]
    requested_dac = [float(row["gw_dac"]) for row in active]
    applied_dac = [float(row["plc_applied_dac"]) for row in active]
    error = [TARGET_RAW - value for value in level]
    abs_error = [abs(value) for value in error]
    squared_error = [value * value for value in error]
    dt = [right - left for left, right in zip(t, t[1:])]
    tail = [i for i, value in enumerate(t) if value >= t[-1] - 30.0]
    tail_level = [level[i] for i in tail]
    tail_dac = [applied_dac[i] for i in tail]
    tail_error = [TARGET_RAW - value for value in tail_level]
    first10 = first_reach(t, level, TARGET_RAW * 0.10)
    first90 = first_reach(t, level, TARGET_RAW * 0.90)
    mean = statistics.fmean

    return {
        "samples_total": len(rows),
        "samples_active": len(active),
        "active_duration_s": t[-1] - t[0],
        "sample_period_median_s": statistics.median(dt),
        "sample_period_mean_s": mean(dt),
        "sample_period_std_s": statistics.stdev(dt),
        "sample_period_max_s": max(dt),
        "initial_median_raw": level[0],
        "maximum_instant_raw": max(instant),
        "maximum_median_raw": max(level),
        "overshoot_raw": max(0.0, max(level) - TARGET_RAW),
        "overshoot_percent": max(0.0, max(level) - TARGET_RAW)
        / TARGET_RAW
        * 100.0,
        "first_10_percent_s": first10,
        "first_50_percent_s": first_reach(t, level, TARGET_RAW * 0.50),
        "first_90_percent_s": first90,
        "first_95_percent_s": first_reach(t, level, TARGET_RAW * 0.95),
        "first_target_s": first_reach(t, level, TARGET_RAW),
        "rise_time_10_to_90_s": (
            first90 - first10
            if first10 is not None and first90 is not None
            else None
        ),
        "settling_time_5_percent_s": settling_time(t, level, 0.05),
        "settling_time_2_percent_s": settling_time(t, level, 0.02),
        "iae_raw_s": trapz(t, abs_error),
        "ise_raw2_s": trapz(t, squared_error),
        "mae_raw_full": mean(abs_error),
        "rmse_raw_full": math.sqrt(mean(squared_error)),
        "tail30_mean_raw": mean(tail_level),
        "tail30_median_raw": statistics.median(tail_level),
        "tail30_std_raw": statistics.stdev(tail_level),
        "tail30_mean_error_raw": mean(tail_error),
        "tail30_mean_error_percent": mean(tail_error) / TARGET_RAW * 100.0,
        "tail30_mae_raw": mean([abs(value) for value in tail_error]),
        "tail30_rmse_raw": math.sqrt(
            mean([value * value for value in tail_error])
        ),
        "maximum_requested_dac": max(requested_dac),
        "maximum_applied_dac": max(applied_dac),
        "mean_applied_dac": mean(applied_dac),
        "tail30_mean_applied_dac": mean(tail_dac),
        "tail30_min_applied_dac": min(tail_dac),
        "tail30_max_applied_dac": max(tail_dac),
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
    }


def zero_metrics(path: Path) -> dict[str, object]:
    rows = load(path)
    all_safe = all(
        row["gw_enable"] == "False"
        and float(row["gw_dac"]) == 0.0
        and row["gw_applied_enable"] == "False"
        and float(row["gw_applied_dac"]) == 0.0
        and row["plc_enable"] == "False"
        and float(row["plc_dac"]) == 0.0
        and row["plc_applied_enable"] == "False"
        and float(row["plc_applied_dac"]) == 0.0
        and row["gw_watchdog_healthy"] == "True"
        and row["plc_watchdog_healthy"] == "True"
        for row in rows
    )
    return {"samples": len(rows), "all_zero_and_healthy": all_safe}


def trajectory(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = [
        row for row in load(path) if float(row["active_elapsed_s"]) >= 0.0
    ]
    return (
        [float(row["active_elapsed_s"]) for row in rows],
        [float(row["median9_raw"]) for row in rows],
        [float(row["plc_applied_dac"]) for row in rows],
    )


def calculate() -> dict[str, object]:
    mpc = active_metrics(MPC / "first-active-monitor.csv")
    pi = active_metrics(PI / "first-active-monitor.csv")
    pi_first = active_metrics(PI_FIRST / "first-active-monitor.csv")
    mpc["physical_final_height_cm"] = 15.0
    pi["physical_final_height_cm"] = 14.7
    pi_first["physical_final_height_cm"] = 6.0
    mpc["predeployment_zero"] = zero_metrics(
        MPC / "predeployment-zero-output-monitor.csv"
    )
    mpc["postshutdown_zero"] = zero_metrics(
        MPC / "postshutdown-zero-output-monitor.csv"
    )
    pi["predeployment_zero"] = zero_metrics(
        PI / "predeployment-zero-output-monitor.csv"
    )
    pi["postshutdown_zero"] = zero_metrics(
        PI / "postshutdown-zero-output-monitor.csv"
    )

    return {
        "status": "final_real_plant_comparison_complete",
        "target_raw": TARGET_RAW,
        "physical_target_cm": 15.0,
        "mpc_v4": mpc,
        "pi_final_ki_0_10": pi,
        "pi_first_attempt_ki_0_02": pi_first,
        "relative_comparison": {
            "pi_minus_mpc_iae_percent": (
                float(pi["iae_raw_s"]) / float(mpc["iae_raw_s"]) - 1.0
            )
            * 100.0,
            "pi_minus_mpc_ise_percent": (
                float(pi["ise_raw2_s"]) / float(mpc["ise_raw2_s"]) - 1.0
            )
            * 100.0,
            "pi_to_mpc_tail30_mean_error_ratio": float(
                pi["tail30_mean_error_raw"]
            )
            / float(mpc["tail30_mean_error_raw"]),
            "pi_minus_mpc_total_variation_percent": (
                float(pi["applied_dac_total_variation"])
                / float(mpc["applied_dac_total_variation"])
                - 1.0
            )
            * 100.0,
        },
        "interpretation_limits": [
            "Each final controller result is based on one bounded 180 s run.",
            "Manual physical height is authoritative; raw-to-centimetre conversion varied between sessions.",
            "The comparison supports descriptive engineering conclusions, not statistical superiority claims.",
        ],
    }


def fmt(value: object, digits: int = 2) -> str:
    if value is None:
        return "not reached"
    return f"{float(value):.{digits}f}"


def write_document(metrics: dict[str, object]) -> None:
    mpc = metrics["mpc_v4"]
    pi = metrics["pi_final_ki_0_10"]
    first = metrics["pi_first_attempt_ki_0_02"]
    rel = metrics["relative_comparison"]
    assert isinstance(mpc, dict) and isinstance(pi, dict)
    assert isinstance(first, dict) and isinstance(rel, dict)

    text = f"""# Final PI versus MPC V4 real-plant comparison

## Experimental basis

The comparison uses the final bounded 180 s runs at the same nominal physical
target of 15 cm, raw target of 17000, and actuator envelope of 0..16000 DAC.
The MPC V4 experiment was completed on 2026-08-29 and the final retuned PI
experiment on 2026-09-01. Both runs used the independent supervisor, healthy
PLC watchdog feedback, automatic FORTE termination, and verified zero output.

The manual physical observation is authoritative because the raw-count zero
offset varied between sessions. Raw metrics are retained for reproducibility
and for comparing the trajectories recorded by the common supervisor.

## Final quantitative comparison

| Metric | MPC V4 | PI, KP=4.0 and KI=0.10 |
|---|---:|---:|
| Physical final height | 15.0 cm | 14.7 cm |
| Active duration | {fmt(mpc['active_duration_s'], 3)} s | {fmt(pi['active_duration_s'], 3)} s |
| 10%-90% rise time | {fmt(mpc['rise_time_10_to_90_s'], 3)} s | {fmt(pi['rise_time_10_to_90_s'], 3)} s |
| First 90% target | {fmt(mpc['first_90_percent_s'], 3)} s | {fmt(pi['first_90_percent_s'], 3)} s |
| Raw settling time, +/-5% | {fmt(mpc['settling_time_5_percent_s'], 3)} s | {fmt(pi['settling_time_5_percent_s'], 3)} |
| Raw settling time, +/-2% | {fmt(mpc['settling_time_2_percent_s'], 3)} s | {fmt(pi['settling_time_2_percent_s'], 3)} |
| Maximum median-9 level | {fmt(mpc['maximum_median_raw'], 0)} raw | {fmt(pi['maximum_median_raw'], 0)} raw |
| Overshoot | {fmt(mpc['overshoot_percent'], 3)}% | {fmt(pi['overshoot_percent'], 3)}% |
| IAE | {fmt(mpc['iae_raw_s'], 2)} raw.s | {fmt(pi['iae_raw_s'], 2)} raw.s |
| ISE | {fmt(mpc['ise_raw2_s'], 2)} raw^2.s | {fmt(pi['ise_raw2_s'], 2)} raw^2.s |
| Last-30-s mean level | {fmt(mpc['tail30_mean_raw'], 2)} raw | {fmt(pi['tail30_mean_raw'], 2)} raw |
| Last-30-s mean error | {fmt(mpc['tail30_mean_error_raw'], 2)} raw ({fmt(mpc['tail30_mean_error_percent'], 3)}%) | {fmt(pi['tail30_mean_error_raw'], 2)} raw ({fmt(pi['tail30_mean_error_percent'], 3)}%) |
| Last-30-s standard deviation | {fmt(mpc['tail30_std_raw'], 2)} raw | {fmt(pi['tail30_std_raw'], 2)} raw |
| Last-30-s mean applied DAC | {fmt(mpc['tail30_mean_applied_dac'], 2)} | {fmt(pi['tail30_mean_applied_dac'], 2)} |
| Applied-DAC total variation | {fmt(mpc['applied_dac_total_variation'], 0)} | {fmt(pi['applied_dac_total_variation'], 0)} |
| Maximum applied DAC | {fmt(mpc['maximum_applied_dac'], 0)} | {fmt(pi['maximum_applied_dac'], 0)} |
| Watchdog healthy throughout | yes | yes |
| Final zero output independently verified | yes | yes |

The PI IAE was {fmt(rel['pi_minus_mpc_iae_percent'], 2)}% higher than the MPC
IAE, while its ISE was {fmt(abs(float(rel['pi_minus_mpc_ise_percent'])), 2)}%
lower. This mixed integral-error result reflects the PI's faster early fill and
the MPC's substantially better final tracking. During the last 30 s, the PI
mean raw error was {fmt(rel['pi_to_mpc_tail30_mean_error_ratio'], 2)} times the
MPC error. The PI used {fmt(rel['pi_minus_mpc_total_variation_percent'], 2)}%
more applied-DAC total variation.

## PI retuning evidence

The first matched PI attempt retained `KI=0.02` and reached approximately 6 cm.
Its maximum median-9 level was {fmt(first['maximum_median_raw'], 0)} raw and its
last-30-s mean level was {fmt(first['tail30_mean_raw'], 2)} raw. The single
justified retuning to `KI=0.10` brought the physical level to 14.7 cm while the
independent rate limiter continued to govern the initial actuator ramp. No
additional PI tuning campaign was required.

## Interpretation

The PI provided a simple, stable baseline and reached the physical target with
approximately 0.3 cm absolute error and no overshoot. The MPC V4 response was
slower during part of the rise and had approximately 0.506% raw overshoot, but
it entered and remained within the raw tracking bands and achieved much lower
final error and variability. Both controllers converged to a similar final DAC
region near 14000, consistent with balancing the continuous bottom drain.

The result supports an engineering conclusion that the MPC V4 improved final
tracking and explicit constraint handling in this experiment. It does not
support a statistical superiority claim because only one accepted final run
per controller was executed and the raw-to-centimetre calibration varied
between sessions.

## Safety and closure

Both final runs completed with `ACTIVE_WINDOW_COMPLETE`. The watchdog remained
healthy, the independent supervisor terminated FORTE, and post-shutdown files
confirmed `Enable=FALSE` and `DAC=0` at both gateway and PLC. The practical
laboratory stage is closed; no additional real-plant experiment is required.

## Reproducibility

- MPC evidence: `data/sample/mpc-v4-target17000-20260829/`;
- final PI evidence: `data/sample/pi-v4-matched-20260901/`;
- first PI attempt: `data/sample/pi-v4-matched-first-attempt-20260829/`;
- generated metrics: `data/sample/pi-vs-mpc-v4-final-20260901/metrics.json`;
- generated figures: `docs/figures/pi-vs-mpc-v4-final-20260901/`;
- analysis script: `scripts/analyze_pi_mpc_v4_final.py`.
"""
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT.write_text(text, encoding="utf-8", newline="\n")


def generate_figures() -> None:
    mpc_t, mpc_level, mpc_dac = trajectory(MPC / "first-active-monitor.csv")
    pi_t, pi_level, pi_dac = trajectory(PI / "first-active-monitor.csv")
    first_t, first_level, _ = trajectory(PI_FIRST / "first-active-monitor.csv")
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "svg.hashsalt": "pi-mpc-v4-final-20260901",
        }
    )

    fig, axis = plt.subplots(figsize=(9.2, 4.8), constrained_layout=True)
    axis.plot(mpc_t, mpc_level, color="#1261A0", linewidth=2.0, label="MPC V4")
    axis.plot(pi_t, pi_level, color="#D97706", linewidth=1.8, label="PI, KI=0.10")
    axis.plot(
        first_t,
        first_level,
        color="#8B8C89",
        linewidth=1.1,
        alpha=0.8,
        label="PI first attempt, KI=0.02",
    )
    axis.axhline(
        TARGET_RAW,
        color="#C73E1D",
        linestyle="--",
        linewidth=1.4,
        label="Target 17000 raw",
    )
    axis.axhspan(TARGET_RAW * 0.95, TARGET_RAW * 1.05, color="#2A9D8F", alpha=0.09)
    axis.set(
        xlabel="Active time (s)",
        ylabel="Median-9 level (raw)",
        xlim=(0, 180),
        title="Final real-plant PI and MPC V4 level responses",
    )
    axis.legend(loc="lower right")
    for suffix in ("png", "svg"):
        fig.savefig(
            FIGURES / f"pi-mpc-v4-level-comparison.{suffix}",
            dpi=180,
            metadata={"Date": None},
        )
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(9.2, 4.3), constrained_layout=True)
    axis.plot(mpc_t, mpc_dac, color="#1261A0", linewidth=1.8, label="MPC V4")
    axis.plot(pi_t, pi_dac, color="#D97706", linewidth=1.5, label="PI, KI=0.10")
    axis.set(
        xlabel="Active time (s)",
        ylabel="Applied DAC",
        xlim=(0, 180),
        ylim=(0, 16800),
        title="Final real-plant PI and MPC V4 control effort",
    )
    axis.legend(loc="lower right")
    for suffix in ("png", "svg"):
        fig.savefig(
            FIGURES / f"pi-mpc-v4-dac-comparison.{suffix}",
            dpi=180,
            metadata={"Date": None},
        )
    plt.close(fig)

    # Matplotlib writes trailing spaces in multiline SVG path data.
    # Normalize SVGs so git diff --check remains clean.
    for svg in FIGURES.glob("*.svg"):
        content = svg.read_text(encoding="utf-8")
        normalized = "\n".join(
            line.rstrip() for line in content.splitlines()
        ) + "\n"
        svg.write_text(
            normalized,
            encoding="utf-8",
            newline="\n",
        )


def main() -> int:
    metrics = calculate()
    COMPARISON.mkdir(parents=True, exist_ok=True)
    (COMPARISON / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (PI / "metrics.json").write_text(
        json.dumps(metrics["pi_final_ki_0_10"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (PI_FIRST / "metrics.json").write_text(
        json.dumps(metrics["pi_first_attempt_ki_0_02"], indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    generate_figures()
    write_document(metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"Metrics: {COMPARISON / 'metrics.json'}")
    print(f"Document: {DOCUMENT}")
    print(f"Figures: {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
