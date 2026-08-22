from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3G_PATH = ROOT / "scripts" / "mpc_reference_controller_v3g.py"
EVIDENCE = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3e-expanded-60s-20260822"
    / "expanded-active-monitor.csv"
)

spec = importlib.util.spec_from_file_location("mpc_reference_controller_v3g", V3G_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


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
        raise RuntimeError("Insufficient V3E ACTIVE evidence.")

    def nearest(t):
        return min(rows, key=lambda r: abs(r["t"] - t))

    # Resample to the 500 ms controller grid.
    grid = []
    t = rows[0]["t"]
    while t <= rows[-1]["t"] + 1e-9:
        grid.append({"t": t, **nearest(t)})
        t += 0.5

    model = mod.load_default_model()
    config = mod.default_v3e_config()
    v3g = mod.SafeDelayedMoveBlockedNMPCV3G(
        model,
        config=config,
        bias_alpha=0.10,
    )

    # Canonical V3 comparator.
    canonical = mod.v3.SafeDelayedMoveBlockedNMPCV3(
        model,
        config=config,
    )

    delay_steps = 18
    records = []

    for k in range(delay_steps, len(grid)):
        current = grid[k]
        previous = grid[k - 1]
        delayed = grid[k - delay_steps]["applied"]

        v3g.observe_and_update_bias(
            measured_raw=current["med"],
            previous_measured_raw=previous["med"],
            delayed_applied_dac=delayed,
        )

        history = tuple(
            grid[j]["applied"]
            for j in range(k - delay_steps, k)
        )

        if current["med"] <= 450.0 or current["applied"] < 11800.0:
            continue

        v3g_best, _ = v3g.choose_command(
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
                canonical_candidates.append(
                    {
                        "target": float(target),
                        "cost": float(cost),
                    }
                )

        canonical_best = (
            min(canonical_candidates, key=lambda x: x["cost"])
            if canonical_candidates
            else None
        )

        canonical_command = (
            None
            if canonical_best is None
            else mod.SafeDelayedMoveBlockedNMPCV3G.rate_limited_command(
                current["applied"],
                canonical_best["target"],
                maximum_delta_dac=750.0,
            )
        )

        records.append(
            {
                "t": current["t"],
                "med": current["med"],
                "applied": current["applied"],
                "bias": v3g.bias_raw,
                "canonical_target": None if canonical_best is None else canonical_best["target"],
                "canonical_command": canonical_command,
                "v3g_target": None if v3g_best is None else v3g_best["target"],
                "v3g_command": None if v3g_best is None else v3g_best["command_dac"],
            }
        )

    if len(records) < 20:
        raise RuntimeError("Too few high-DAC above-SP replay records.")

    canonical_down = sum(
        r["canonical_command"] is not None
        and r["canonical_command"] < r["applied"] - 1e-9
        for r in records
    )
    v3g_down = sum(
        r["v3g_command"] is not None
        and r["v3g_command"] < r["applied"] - 1e-9
        for r in records
    )

    canonical_fraction = canonical_down / len(records)
    v3g_fraction = v3g_down / len(records)

    final_bias = records[-1]["bias"]
    positive_bias_fraction = sum(r["bias"] > 0.0 for r in records) / len(records)

    classification = (
        "V3G_REAL_TRACE_DECISION_REPLAY_PASSED"
        if (
            v3g_fraction >= 0.60
            and v3g_fraction >= canonical_fraction + 0.30
            and final_bias > 0.0
        )
        else "V3G_REAL_TRACE_DECISION_REPLAY_NOT_YET_ACCEPTED"
    )

    result = {
        "classification": classification,
        "record_count": len(records),
        "canonical_downward_command_fraction": canonical_fraction,
        "v3g_downward_command_fraction": v3g_fraction,
        "final_bias_raw": final_bias,
        "positive_bias_fraction": positive_bias_fraction,
        "records": records,
    }

    out_dir = ROOT / "results" / "mpc-v3g-real-trace-replay-20260822"
    out_dir.mkdir(parents=True, exist_ok=False)
    out_json = out_dir / "replay.json"
    out_json.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("MPC V3G REAL-TRACE DECISION REPLAY")
    print("==================================")
    print(f"records:                       {len(records)}")
    print(f"canonical downward fraction:  {100.0*canonical_fraction:.1f}%")
    print(f"V3G downward fraction:        {100.0*v3g_fraction:.1f}%")
    print(f"final learned bias:           {final_bias:+.3f} raw")
    print(f"positive-bias fraction:       {100.0*positive_bias_fraction:.1f}%")
    print(f"classification:                {classification}")
    print()
    print("SELECTED REPLAY POINTS")
    print("----------------------")

    step = max(1, len(records) // 8)
    for r in records[::step][:8]:
        print(
            f"t={r['t']:6.2f}s | Med9={r['med']:7.1f} | "
            f"Applied={r['applied']:7.1f} | Bias={r['bias']:+7.1f} | "
            f"V3cmd={str(r['canonical_command']):>8} | "
            f"V3Gcmd={str(r['v3g_command']):>8}"
        )

    if classification != "V3G_REAL_TRACE_DECISION_REPLAY_PASSED":
        raise RuntimeError(
            "V3G did not produce sufficiently stronger downward action "
            "on the preserved high-DAC above-SP real trace."
        )

    print()
    print("V3G REAL-TRACE DECISION REPLAY: PASSED")
    print(f"RESULT: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
