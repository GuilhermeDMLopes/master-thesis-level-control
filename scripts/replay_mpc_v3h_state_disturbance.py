from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "mpc_reference_controller_v3h.py"
EVIDENCE = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3e-expanded-60s-20260822"
    / "expanded-active-monitor.csv"
)
LONG_DIAG = (
    ROOT
    / "results"
    / "mpc-v3e-model-cost-delay-diagnosis-20260822"
    / "diagnosis.json"
)

spec = importlib.util.spec_from_file_location("mpc_reference_controller_v3h_replay", MODULE)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)


def main() -> int:
    rows = []

    with EVIDENCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            if r["phase"].strip().upper() != "ACTIVE":
                continue
            rows.append(
                {
                    "t": float(r["elapsed_s"]),
                    "med": float(r["median9_raw"]),
                    "applied": float(r["applied_dac"]),
                }
            )

    rows.sort(key=lambda x: x["t"])

    if len(rows) < 100:
        raise RuntimeError("Insufficient preserved V3E ACTIVE evidence.")

    long_diag = json.loads(LONG_DIAG.read_text(encoding="utf-8"))
    future_error = abs(
        float(long_diag["median_eq_predicted_final_vs_real_future_error_raw"])
    )

    def nearest(t: float):
        return min(rows, key=lambda r: abs(r["t"] - t))

    grid = []
    t = rows[0]["t"]
    while t <= rows[-1]["t"] + 1e-9:
        r = nearest(t)
        grid.append(
            {
                "t": t,
                "med": r["med"],
                "applied": r["applied"],
            }
        )
        t += 0.5

    model = m.load_default_model()
    config = m.default_v3e_config()

    v3h = m.SafeDelayedMoveBlockedNMPCV3H(
        model,
        config=config,
        disturbance_alpha=0.10,
    )

    canonical = m.v3.SafeDelayedMoveBlockedNMPCV3(
        model,
        config=config,
    )

    delay_steps = int(model.transport_delay_steps)

    deadzone = 11750.0
    records = []
    premature = []

    for k in range(delay_steps, len(grid)):
        current = grid[k]
        previous = grid[k - 1]
        delayed = grid[k - delay_steps]["applied"]

        v3h.observe_and_update_disturbance(
            measured_raw=current["med"],
            previous_measured_raw=previous["med"],
            delayed_applied_dac=delayed,
        )

        history = tuple(
            grid[j]["applied"]
            for j in range(k - delay_steps, k)
        )

        v3h_best, _ = v3h.choose_command(
            measured_raw=current["med"],
            applied_dac=current["applied"],
            requested_setpoint=450.0,
            history_snapshot=history,
        )

        canonical_candidates = []
        for target in canonical.target_candidates:
            feasible, cost, pmax, pfinal = canonical._predict_candidate(
                measured_raw=current["med"],
                applied_dac=current["applied"],
                requested_setpoint=450.0,
                target_dac=target,
                history_snapshot=history,
            )
            if feasible:
                command = m.v3._rate_limit(
                    current["applied"],
                    target,
                    config.maximum_delta_dac,
                    config.minimum_dac,
                    config.maximum_dac,
                )
                canonical_candidates.append(
                    {
                        "target": float(target),
                        "cost": float(cost),
                        "command": float(command),
                    }
                )

        canonical_best = (
            min(canonical_candidates, key=lambda x: x["cost"])
            if canonical_candidates
            else None
        )

        if v3h_best is None or canonical_best is None:
            continue

        applied_effect = v3h.input_effect_raw_per_step(current["applied"])
        v3h_effect = v3h.input_effect_raw_per_step(v3h_best["command_dac"])
        canonical_effect = v3h.input_effect_raw_per_step(canonical_best["command"])

        def reduction_fraction(after_effect: float) -> float:
            if applied_effect <= 1e-12:
                return 0.0
            return max(
                0.0,
                min(
                    1.0,
                    (applied_effect - after_effect) / applied_effect,
                ),
            )

        rec = {
            "t": current["t"],
            "med": current["med"],
            "applied": current["applied"],
            "disturbance_hat": v3h.disturbance_hat_raw_per_step,
            "steady_shift": v3h.equivalent_steady_shift_raw,
            "canonical_target": canonical_best["target"],
            "canonical_command": canonical_best["command"],
            "canonical_effect_reduction_fraction": reduction_fraction(canonical_effect),
            "v3h_target": v3h_best["target"],
            "v3h_command": v3h_best["command_dac"],
            "v3h_effect_reduction_fraction": reduction_fraction(v3h_effect),
            "v3h_at_or_below_deadzone": v3h_best["command_dac"] <= deadzone + 1e-9,
        }

        if current["med"] > 450.0 and current["applied"] >= 11800.0:
            records.append(rec)

        if current["med"] <= 400.0 and current["applied"] >= 11800.0:
            premature.append(rec)

    if len(records) < 20:
        raise RuntimeError("Too few V3H post-SP high-DAC replay records.")

    deadzone_fraction = sum(r["v3h_at_or_below_deadzone"] for r in records) / len(records)
    effect90_fraction = sum(r["v3h_effect_reduction_fraction"] >= 0.90 for r in records) / len(records)
    canonical_effect90_fraction = sum(r["canonical_effect_reduction_fraction"] >= 0.90 for r in records) / len(records)

    premature_fraction = (
        sum(r["v3h_at_or_below_deadzone"] for r in premature) / len(premature)
        if premature
        else 0.0
    )

    final_shift = records[-1]["steady_shift"]
    shift_error = abs(final_shift - future_error)
    shift_relative_error = shift_error / future_error if future_error > 0 else 0.0

    classification = (
        "V3H_REAL_TRACE_REPLAY_PASSED"
        if (
            deadzone_fraction >= 0.75
            and effect90_fraction >= 0.75
            and canonical_effect90_fraction <= 0.05
            and premature_fraction <= 0.05
            and shift_relative_error <= 0.10
        )
        else "V3H_REAL_TRACE_REPLAY_NOT_ACCEPTED"
    )

    result = {
        "classification": classification,
        "record_count": len(records),
        "premature_record_count": len(premature),
        "deadzone_or_below_fraction_post_sp": deadzone_fraction,
        "v3h_effective_input_reduction_ge_90_fraction": effect90_fraction,
        "canonical_effective_input_reduction_ge_90_fraction": canonical_effect90_fraction,
        "premature_deadzone_fraction_pre_sp_le_400": premature_fraction,
        "final_equivalent_steady_shift_raw": final_shift,
        "observed_future_error_raw": future_error,
        "steady_shift_absolute_error_raw": shift_error,
        "steady_shift_relative_error_fraction": shift_relative_error,
        "records": records,
    }

    out_dir = ROOT / "results" / "mpc-v3h-real-trace-replay-20260822"
    out_dir.mkdir(parents=True, exist_ok=False)
    out_json = out_dir / "replay.json"
    out_json.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("MPC V3H PRESERVED REAL-TRACE REPLAY")
    print("===================================")
    print(f"records:                             {len(records)}")
    print(f"V3H command <= deadzone:             {100.0*deadzone_fraction:.1f}%")
    print(f"V3H effective-input reduction >=90%: {100.0*effect90_fraction:.1f}%")
    print(f"V3 canonical effective >=90%:        {100.0*canonical_effect90_fraction:.1f}%")
    print(f"premature deadzone <=400 raw:        {100.0*premature_fraction:.1f}%")
    print(f"final V3H steady shift:               {final_shift:+.1f} raw")
    print(f"independent future error:             {future_error:.1f} raw")
    print(f"shift mismatch:                       {shift_error:.1f} raw")
    print(f"classification:                       {classification}")
    print()

    step = max(1, len(records) // 8)
    print("REPRESENTATIVE POINTS")
    print("---------------------")
    for r in records[::step][:8]:
        print(
            f"t={r['t']:6.2f}s | Med9={r['med']:7.1f} | "
            f"d={r['disturbance_hat']:+6.2f} | shift={r['steady_shift']:+7.1f} | "
            f"V3cmd={r['canonical_command']:8.3f} | "
            f"V3Hcmd={r['v3h_command']:8.3f} | "
            f"V3H eff red={100.0*r['v3h_effect_reduction_fraction']:5.1f}%"
        )

    if classification != "V3H_REAL_TRACE_REPLAY_PASSED":
        raise RuntimeError("V3H preserved-real-trace replay did not meet acceptance criteria.")

    print()
    print("V3H PRESERVED REAL-TRACE REPLAY: PASSED")
    print(f"RESULT: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
