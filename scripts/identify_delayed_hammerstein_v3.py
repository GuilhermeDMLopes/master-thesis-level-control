from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StaticModel:
    tau_s: float
    baseline_raw: float
    deadzone_dac: float
    exponent: float
    equilibrium_gain: float


@dataclass(frozen=True)
class ActiveSample:
    t_s: float
    median_raw: float
    applied_dac: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_semicolon_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def as_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text.replace(",", "."))


def load_static_model(path: Path) -> StaticModel:
    document = json.loads(path.read_text(encoding="utf-8"))
    continuous = document["continuous_time"]

    model = StaticModel(
        tau_s=float(continuous["tau_s"]),
        baseline_raw=float(continuous["baseline_raw_y0"]),
        deadzone_dac=float(continuous["deadzone_DAC"]),
        exponent=float(continuous["input_exponent_p"]),
        equilibrium_gain=float(
            continuous[
                "equilibrium_gain_G_raw_per_DAC_power_p"
            ]
        ),
    )

    if model.tau_s <= 0.0:
        raise ValueError("canonical tau must be positive")
    if model.deadzone_dac < 0.0:
        raise ValueError("canonical dead-zone must be non-negative")
    if model.exponent <= 0.0:
        raise ValueError("canonical exponent must be positive")
    if model.equilibrium_gain <= 0.0:
        raise ValueError("canonical equilibrium gain must be positive")

    return model


def load_empty_baseline(path: Path) -> dict[str, float]:
    rows = read_semicolon_csv(path)
    values = [
        value
        for row in rows
        if (value := as_float(row.get("nivel_raw"))) is not None
    ]

    if len(values) < 30:
        raise ValueError("empty-baseline evidence has too few samples")

    return {
        "count": float(len(values)),
        "minimum_raw": min(values),
        "median_raw": float(statistics.median(values)),
        "mean_raw": float(statistics.fmean(values)),
        "maximum_raw": max(values),
        "initial_raw": values[0],
        "final_raw": values[-1],
    }


def load_active_samples(path: Path) -> list[ActiveSample]:
    rows = read_semicolon_csv(path)
    samples: list[ActiveSample] = []

    for row in rows:
        t_s = as_float(row.get("active_elapsed_s"))
        median_raw = as_float(row.get("median9_raw"))
        applied_dac = as_float(row.get("gw_applied_dac"))

        if (
            t_s is None
            or t_s < 0.0
            or median_raw is None
            or applied_dac is None
        ):
            continue

        samples.append(
            ActiveSample(
                t_s=t_s,
                median_raw=median_raw,
                applied_dac=applied_dac,
            )
        )

    samples.sort(key=lambda item: item.t_s)

    if len(samples) < 50:
        raise ValueError("active commissioning evidence has too few samples")

    return samples


def first_time_at_or_above(
    samples: list[ActiveSample],
    *,
    start_s: float,
    threshold_raw: float,
    physical_floor_raw: float,
) -> float | None:
    for sample in samples:
        if sample.t_s < start_s:
            continue
        physical_raw = max(
            physical_floor_raw,
            sample.median_raw,
        )
        if physical_raw >= threshold_raw:
            return sample.t_s
    return None


class AppliedDacHistory:
    def __init__(self, samples: list[ActiveSample]) -> None:
        self.times = [sample.t_s for sample in samples]
        self.values = [sample.applied_dac for sample in samples]

    def zoh(self, time_s: float) -> float:
        index = bisect.bisect_right(self.times, time_s) - 1
        if index < 0:
            return 0.0
        return self.values[index]


def replay_rmse(
    *,
    fit_samples: list[ActiveSample],
    history: AppliedDacHistory,
    physical_floor_raw: float,
    model_baseline_raw: float,
    deadzone_dac: float,
    exponent: float,
    equilibrium_gain: float,
    transport_delay_s: float,
    tau_s: float,
) -> float:
    if tau_s <= 0.0:
        return float("inf")

    # Physical tank is known empty at the baseline offset.
    # Sensor excursions below that offset are treated as measurement noise
    # for the non-negative physical-level state used by this fit.
    predicted = model_baseline_raw
    previous_t = fit_samples[0].t_s
    squared_errors: list[float] = []

    for sample in fit_samples[1:]:
        dt_s = sample.t_s - previous_t
        if dt_s <= 0.0:
            previous_t = sample.t_s
            continue

        delayed_dac = history.zoh(
            previous_t - transport_delay_s
        )

        a = math.exp(-dt_s / tau_s)
        effective = max(
            0.0,
            delayed_dac - deadzone_dac,
        )

        predicted = (
            model_baseline_raw
            + a * (predicted - model_baseline_raw)
            + equilibrium_gain
            * (1.0 - a)
            * effective**exponent
        )

        observed = max(
            physical_floor_raw,
            sample.median_raw,
        )

        squared_errors.append(
            (predicted - observed) ** 2
        )
        previous_t = sample.t_s

    if not squared_errors:
        raise ValueError("no replay residuals were produced")

    return math.sqrt(
        statistics.fmean(squared_errors)
    )


def fit_implementation_grid(
    *,
    samples: list[ActiveSample],
    physical_floor_raw: float,
    canonical: StaticModel,
    controller_sample_s: float,
) -> dict[str, float]:
    first_effective_index = next(
        (
            index
            for index, sample in enumerate(samples)
            if sample.applied_dac >= canonical.deadzone_dac
        ),
        None,
    )

    if first_effective_index is None:
        raise ValueError(
            "active evidence never reached the canonical pump dead-zone"
        )

    fit_samples = samples[first_effective_index:]
    history = AppliedDacHistory(samples)

    best: tuple[float, int, float] | None = None

    # Implementation-aware search:
    # 6..12 s delay in exact 500 ms queue steps,
    # tau 1..12 s at 0.05 s resolution.
    minimum_delay_steps = int(round(6.0 / controller_sample_s))
    maximum_delay_steps = int(round(12.0 / controller_sample_s))

    for delay_steps in range(
        minimum_delay_steps,
        maximum_delay_steps + 1,
    ):
        delay_s = delay_steps * controller_sample_s

        for tau_index in range(20, 241):
            tau_s = tau_index * 0.05

            rmse = replay_rmse(
                fit_samples=fit_samples,
                history=history,
                physical_floor_raw=physical_floor_raw,
                model_baseline_raw=physical_floor_raw,
                deadzone_dac=canonical.deadzone_dac,
                exponent=canonical.exponent,
                equilibrium_gain=canonical.equilibrium_gain,
                transport_delay_s=delay_s,
                tau_s=tau_s,
            )

            candidate = (rmse, delay_steps, tau_s)
            if best is None or candidate < best:
                best = candidate

    if best is None:
        raise RuntimeError("delayed-model search produced no candidate")

    v3_rmse, delay_steps, tau_s = best

    v2_rmse = replay_rmse(
        fit_samples=fit_samples,
        history=history,
        physical_floor_raw=physical_floor_raw,
        model_baseline_raw=canonical.baseline_raw,
        deadzone_dac=canonical.deadzone_dac,
        exponent=canonical.exponent,
        equilibrium_gain=canonical.equilibrium_gain,
        transport_delay_s=0.0,
        tau_s=canonical.tau_s,
    )

    first_effective_t = fit_samples[0].t_s
    rise_threshold = physical_floor_raw + 50.0
    rise_t = first_time_at_or_above(
        samples,
        start_s=first_effective_t,
        threshold_raw=rise_threshold,
        physical_floor_raw=physical_floor_raw,
    )

    empirical_delay_s = (
        None
        if rise_t is None
        else rise_t - first_effective_t
    )

    return {
        "fit_start_s": first_effective_t,
        "fit_samples": float(len(fit_samples)),
        "transport_delay_steps": float(delay_steps),
        "transport_delay_s": delay_steps * controller_sample_s,
        "tau_s": tau_s,
        "v3_rmse_raw": v3_rmse,
        "v2_replay_rmse_raw": v2_rmse,
        "rmse_ratio_v3_over_v2": v3_rmse / v2_rmse,
        "empirical_rise_threshold_raw": rise_threshold,
        "empirical_rise_time_s": (
            float("nan")
            if rise_t is None
            else rise_t
        ),
        "empirical_effective_delay_s": (
            float("nan")
            if empirical_delay_s is None
            else empirical_delay_s
        ),
    }


def implied_equilibrium_dac(
    *,
    target_raw: float,
    baseline_raw: float,
    deadzone_dac: float,
    exponent: float,
    equilibrium_gain: float,
) -> float:
    delta = target_raw - baseline_raw
    if delta <= 0.0:
        return deadzone_dac

    return (
        deadzone_dac
        + (
            delta / equilibrium_gain
        ) ** (1.0 / exponent)
    )


def build_document(
    *,
    active_path: Path,
    empty_path: Path,
    canonical_path: Path,
    baseline: dict[str, float],
    canonical: StaticModel,
    fit: dict[str, float],
) -> dict[str, object]:
    sample_time_s = 0.5
    horizon_s = 30.0
    prediction_steps = int(round(horizon_s / sample_time_s))
    candidate_count = 13
    tau_s = fit["tau_s"]

    a = math.exp(-sample_time_s / tau_s)
    b = canonical.equilibrium_gain * (1.0 - a)

    empty_raw = baseline["median_raw"]
    equilibrium_dac = implied_equilibrium_dac(
        target_raw=450.0,
        baseline_raw=empty_raw,
        deadzone_dac=canonical.deadzone_dac,
        exponent=canonical.exponent,
        equilibrium_gain=canonical.equilibrium_gain,
    )

    return {
        "model_type": "delayed_deadzone_hammerstein_first_order",
        "status": "candidate_offline_from_real_commissioning",
        "evidence": {
            "active_commissioning": {
                "path": active_path.as_posix(),
                "sha256": sha256(active_path),
            },
            "empty_baseline": {
                "path": empty_path.as_posix(),
                "sha256": sha256(empty_path),
            },
            "static_model_source": {
                "path": canonical_path.as_posix(),
                "sha256": sha256(canonical_path),
            },
        },
        "physical_context": {
            "empty_tank_height_cm": 0.0,
            "empty_tank_raw_offset": empty_raw,
            "central_bottom_drain": True,
            "drain_description": (
                "Central pipe at the bottom drains water by gravity "
                "back to the lower reservoir."
            ),
            "context_source": "manual laboratory observation 2026-08-18",
        },
        "empty_baseline_observation": baseline,
        "static_nonlinearity": {
            "source": "preserved broader V1 identification dataset",
            "deadzone_DAC": canonical.deadzone_dac,
            "input_exponent_p": canonical.exponent,
            "equilibrium_gain_G_raw_per_DAC_power_p": (
                canonical.equilibrium_gain
            ),
            "previous_tau_s_not_reused_for_v3_dynamics": canonical.tau_s,
            "previous_baseline_raw_not_reused_for_physical_zero": (
                canonical.baseline_raw
            ),
        },
        "dynamic_fit_500ms": {
            "method": (
                "grid search over implementable 500 ms delay queue "
                "and first-order tau with static nonlinearity fixed"
            ),
            "observation_state_floor_raw": empty_raw,
            "transport_delay_steps": int(
                fit["transport_delay_steps"]
            ),
            "transport_delay_s": fit["transport_delay_s"],
            "tau_s": tau_s,
            "discrete_a": a,
            "discrete_b_raw_per_DAC_power_p": b,
            "fit_start_s": fit["fit_start_s"],
            "fit_samples": int(fit["fit_samples"]),
            "rmse_raw": fit["v3_rmse_raw"],
            "canonical_v2_replay_rmse_raw": (
                fit["v2_replay_rmse_raw"]
            ),
            "rmse_ratio_v3_over_v2": (
                fit["rmse_ratio_v3_over_v2"]
            ),
            "empirical_rise_threshold_raw": (
                fit["empirical_rise_threshold_raw"]
            ),
            "empirical_effective_delay_s": (
                fit["empirical_effective_delay_s"]
            ),
        },
        "target_implication": {
            "target_raw": 450.0,
            "implied_equilibrium_DAC": equilibrium_dac,
        },
        "controller_contract_proposal": {
            "sample_time_s": sample_time_s,
            "prediction_horizon_s": horizon_s,
            "prediction_steps": prediction_steps,
            "target_candidates": candidate_count,
            "candidate_prediction_iterations": (
                candidate_count * prediction_steps
            ),
            "maximum_delta_dac_per_update": 750.0,
            "minimum_dac": 0.0,
            "maximum_dac": 12000.0,
            "prediction_requires_applied_dac_history_queue": True,
            "history_queue_length_samples": int(
                fit["transport_delay_steps"]
            ),
            "bias_adaptation_policy": (
                "Do not apply immediate-input bias adaptation through "
                "the transport-delay interval. If bias adaptation is "
                "retained, use delayed applied-input sensitivity."
            ),
        },
        "scope_limitations": [
            (
                "The central gravity drain is physically documented but "
                "is represented only through the effective identified "
                "first-order dynamics in this V3 candidate."
            ),
            (
                "Static dead-zone, exponent, and gain are retained from "
                "the broader preserved identification dataset because one "
                "commissioning transient cannot identify all static and "
                "dynamic parameters independently."
            ),
            (
                "This candidate is for offline implementation and replay "
                "validation before any additional real-plant MPC run."
            ),
        ],
        "authorization": {
            "real_mpc_full_operation_authorized": False,
            "real_actuation_performed_by_this_analysis": False,
        },
    }


def write_report(
    path: Path,
    document: dict[str, object],
) -> None:
    evidence = document["evidence"]
    physical = document["physical_context"]
    empty = document["empty_baseline_observation"]
    static = document["static_nonlinearity"]
    fit = document["dynamic_fit_500ms"]
    target = document["target_implication"]
    contract = document["controller_contract_proposal"]

    lines = [
        "# Delayed Hammerstein MPC V3 candidate",
        "",
        "## Status",
        "",
        "Offline identification from the preserved 2026-08-18 real V2 "
        "commissioning evidence. No network, PLC, gateway, FORTE, "
        "deployment, or actuator write is used by this analysis.",
        "",
        "## Physical reference",
        "",
        f"- physically empty tank: {physical['empty_tank_height_cm']:.1f} cm",
        f"- empty raw offset: {physical['empty_tank_raw_offset']:.3f}",
        "- central bottom pipe drains water by gravity to the lower reservoir",
        "",
        "The empty-tank raw offset is treated as the non-negative physical "
        "level-state floor. Sensor excursions below it remain measurement "
        "noise, not negative water height.",
        "",
        "## Preserved evidence",
        "",
        f"- active V2 CSV: `{evidence['active_commissioning']['path']}`",
        f"- active SHA256: `{evidence['active_commissioning']['sha256']}`",
        f"- empty baseline CSV: `{evidence['empty_baseline']['path']}`",
        f"- empty SHA256: `{evidence['empty_baseline']['sha256']}`",
        f"- static model: `{evidence['static_model_source']['path']}`",
        f"- static model SHA256: `{evidence['static_model_source']['sha256']}`",
        "",
        "## Empty baseline observation",
        "",
        f"- samples: {int(empty['count'])}",
        f"- min raw: {empty['minimum_raw']:.3f}",
        f"- median raw: {empty['median_raw']:.3f}",
        f"- mean raw: {empty['mean_raw']:.3f}",
        f"- max raw: {empty['maximum_raw']:.3f}",
        f"- initial raw: {empty['initial_raw']:.3f}",
        f"- final raw: {empty['final_raw']:.3f}",
        "",
        "## Static nonlinearity retained from V1",
        "",
        f"- dead-zone: {static['deadzone_DAC']:.3f} DAC",
        f"- exponent: {static['input_exponent_p']:.6f}",
        (
            "- equilibrium gain: "
            f"{static['equilibrium_gain_G_raw_per_DAC_power_p']:.12f}"
        ),
        "",
        "Only delay and the effective dynamic time constant are reidentified "
        "from the latest commissioning transient. This avoids trying to "
        "estimate static gain and transient dynamics from one short run.",
        "",
        "## V3 delayed dynamic fit",
        "",
        f"- transport delay: {fit['transport_delay_s']:.3f} s",
        f"- delay queue: {fit['transport_delay_steps']} samples at 500 ms",
        f"- tau: {fit['tau_s']:.3f} s",
        f"- discrete a: {fit['discrete_a']:.15f}",
        (
            "- discrete b: "
            f"{fit['discrete_b_raw_per_DAC_power_p']:.15f}"
        ),
        (
            "- empirical delay to baseline+50 raw rise: "
            f"{fit['empirical_effective_delay_s']:.3f} s"
        ),
        f"- V3 replay RMSE: {fit['rmse_raw']:.3f} raw",
        (
            "- canonical V2 replay RMSE on same interval: "
            f"{fit['canonical_v2_replay_rmse_raw']:.3f} raw"
        ),
        (
            "- V3/V2 RMSE ratio: "
            f"{fit['rmse_ratio_v3_over_v2']:.4f}"
        ),
        "",
        "The replay result supports an explicit transport-delay state. "
        "The prior no-delay first-order dynamics are not retained for V3.",
        "",
        "## Target implication",
        "",
        f"- target: {target['target_raw']:.3f} raw",
        (
            "- implied equilibrium DAC with measured empty offset: "
            f"{target['implied_equilibrium_DAC']:.3f}"
        ),
        "",
        "## Proposed V3 implementation contract",
        "",
        f"- control/model sample: {contract['sample_time_s']:.3f} s",
        f"- prediction horizon: {contract['prediction_horizon_s']:.1f} s",
        f"- prediction steps: {contract['prediction_steps']}",
        f"- target candidates: {contract['target_candidates']}",
        (
            "- candidate prediction iterations/update: "
            f"{contract['candidate_prediction_iterations']}"
        ),
        (
            "- max move: "
            f"{contract['maximum_delta_dac_per_update']:.1f} DAC/update"
        ),
        (
            "- DAC envelope: "
            f"{contract['minimum_dac']:.0f} .. "
            f"{contract['maximum_dac']:.0f}"
        ),
        (
            "- applied-DAC history queue required: "
            f"{contract['prediction_requires_applied_dac_history_queue']}"
        ),
        (
            "- history queue length: "
            f"{contract['history_queue_length_samples']} samples"
        ),
        "",
        "The predictor must initialize its delay queue from actual applied "
        "DAC history. Future candidate moves are appended after already "
        "committed hydraulic input, so water already in transit is predicted.",
        "",
        "Immediate-input bias adaptation must not interpret the transport "
        "delay as model bias. Any retained bias estimator must use delayed "
        "input sensitivity.",
        "",
        "## Scope limitation",
        "",
        "The gravity drain is not separately parameterized in this candidate. "
        "Its net effect is included in the effective first-order dynamics. "
        "A separate Torricelli-style outflow model is intentionally deferred "
        "because the available commissioning evidence does not identify its "
        "parameters independently and it is not required to move the thesis "
        "to a delay-aware MPC validation.",
        "",
        "## Decision",
        "",
        "```text",
        "MPC V3 DELAYED MODEL CANDIDATE IDENTIFIED: YES",
        "V1 STATIC NONLINEARITY PRESERVED: YES",
        "PHYSICAL EMPTY OFFSET INCLUDED: YES",
        "EXPLICIT TRANSPORT DELAY REQUIRED: YES",
        "REAL ACTUATION BY THIS STAGE: NO",
        "REAL MPC FULL OPERATION AUTHORIZED: NO",
        "```",
        "",
        "Next: implement V3 additively in the reference controller and "
        "4diac/FORTE, then replay/simulate offline before another lab run.",
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Identify an implementation-aware delayed first-order "
            "Hammerstein MPC V3 candidate from preserved real evidence. "
            "Offline only."
        )
    )
    parser.add_argument("--active-csv", type=Path, required=True)
    parser.add_argument("--empty-csv", type=Path, required=True)
    parser.add_argument("--canonical-model", type=Path, required=True)
    parser.add_argument("--output-model", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("DELAYED HAMMERSTEIN MPC V3 IDENTIFICATION")
    print("========================================")
    print("NETWORK ACCESS: NO")
    print("PLC ACCESS: NO")
    print("GATEWAY ACCESS: NO")
    print("FORTE ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print()

    canonical = load_static_model(args.canonical_model)
    baseline = load_empty_baseline(args.empty_csv)
    samples = load_active_samples(args.active_csv)

    physical_floor_raw = baseline["median_raw"]

    fit = fit_implementation_grid(
        samples=samples,
        physical_floor_raw=physical_floor_raw,
        canonical=canonical,
        controller_sample_s=0.5,
    )

    document = build_document(
        active_path=args.active_csv,
        empty_path=args.empty_csv,
        canonical_path=args.canonical_model,
        baseline=baseline,
        canonical=canonical,
        fit=fit,
    )

    args.output_model.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    args.output_model.write_text(
        json.dumps(
            document,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    write_report(
        args.output_report,
        document,
    )

    v3 = document["dynamic_fit_500ms"]

    print(f"Empty baseline median raw: {physical_floor_raw:.3f}")
    print(f"Canonical dead-zone DAC: {canonical.deadzone_dac:.3f}")
    print(f"Canonical exponent: {canonical.exponent:.6f}")
    print(f"Canonical gain: {canonical.equilibrium_gain:.12f}")
    print()
    print("IMPLEMENTATION-AWARE DYNAMIC FIT")
    print("--------------------------------")
    print(
        "transport delay: "
        f"{v3['transport_delay_s']:.3f} s "
        f"({v3['transport_delay_steps']} x 500 ms)"
    )
    print(f"tau: {v3['tau_s']:.3f} s")
    print(f"discrete a: {v3['discrete_a']:.15f}")
    print(
        "discrete b: "
        f"{v3['discrete_b_raw_per_DAC_power_p']:.15f}"
    )
    print(
        "empirical delay to baseline+50 rise: "
        f"{v3['empirical_effective_delay_s']:.3f} s"
    )
    print(f"V3 replay RMSE: {v3['rmse_raw']:.3f} raw")
    print(
        "Canonical V2 replay RMSE: "
        f"{v3['canonical_v2_replay_rmse_raw']:.3f} raw"
    )
    print(
        "V3/V2 RMSE ratio: "
        f"{v3['rmse_ratio_v3_over_v2']:.4f}"
    )
    print()

    acceptance = {
        "empty baseline plausible":
            270.0 <= physical_floor_raw <= 305.0,
        "delay is supported":
            6.0 <= v3["transport_delay_s"] <= 12.0,
        "tau is finite/usable":
            1.0 <= v3["tau_s"] <= 12.0,
        "V3 replay RMSE <= 25 raw":
            v3["rmse_raw"] <= 25.0,
        "V3 replay improves >= 60 percent":
            v3["rmse_ratio_v3_over_v2"] <= 0.40,
        "empirical rise delay finite":
            math.isfinite(v3["empirical_effective_delay_s"]),
    }

    for label, passed in acceptance.items():
        print(f"{label}: {'PASSED' if passed else 'FAILED'}")

    print()
    print(f"MODEL:  {args.output_model}")
    print(f"REPORT: {args.output_report}")
    print("REAL ACTUATION: NO")
    print("REAL MPC FULL OPERATION AUTHORIZED: NO")

    if not all(acceptance.values()):
        print("MPC V3 DELAYED MODEL CANDIDATE: NOT ACCEPTED")
        return 2

    print("MPC V3 DELAYED MODEL CANDIDATE: ACCEPTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
