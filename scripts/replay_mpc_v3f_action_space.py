from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "scripts" / "mpc_v3f_action_candidates.py"
EVIDENCE = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3e-expanded-60s-20260822"
    / "expanded-active-monitor.csv"
)

spec = importlib.util.spec_from_file_location("mpc_v3f_action_candidates", KERNEL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def main() -> int:
    rows = []
    with EVIDENCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["phase"].strip().upper() != "ACTIVE":
                continue
            rows.append(
                {
                    "t": float(row["elapsed_s"]),
                    "med": float(row["median9_raw"]),
                    "applied_dac": float(row["applied_dac"]),
                }
            )

    if not rows:
        raise RuntimeError("No ACTIVE V3E evidence rows.")

    above_sp = [r for r in rows if r["med"] > 450.0]
    high_dac_above_sp = [
        r
        for r in above_sp
        if r["applied_dac"] >= 11000.0
    ]

    downward_available = sum(
        1
        for r in high_dac_above_sp
        if mod.has_downward_action(r["applied_dac"])
    )

    if high_dac_above_sp:
        availability_fraction = downward_available / len(high_dac_above_sp)
    else:
        availability_fraction = 0.0

    start = 11850.0
    path = mod.descent_path_to_zero(start)
    updates_to_zero = len(path) - 1
    seconds_to_zero_at_max_negative_move = updates_to_zero * 0.5

    result = {
        "classification": "V3F_CONNECTED_ACTION_SPACE_OFFLINE_TOPOLOGY_PASSED",
        "candidate_count_interior": len(mod.connected_candidates(6000.0)),
        "relative_moves": list(mod.RELATIVE_MOVES),
        "max_move": mod.MAX_MOVE,
        "descent_start_dac": start,
        "descent_path_to_zero": list(path),
        "updates_to_zero_at_max_negative_move": updates_to_zero,
        "seconds_to_zero_at_500ms": seconds_to_zero_at_max_negative_move,
        "v3e_samples_above_sp_and_high_dac": len(high_dac_above_sp),
        "those_samples_with_legal_downward_v3f_action": downward_available,
        "downward_action_availability_fraction": availability_fraction,
    }

    out_dir = ROOT / "results" / "mpc-v3f-action-space-replay-20260822"
    out_dir.mkdir(parents=True, exist_ok=False)
    out_json = out_dir / "action-space-replay.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("MPC V3F CONNECTED ACTION-SPACE OFFLINE REPLAY")
    print("=============================================")
    print(f"interior candidate count:              {result['candidate_count_interior']}")
    print(f"relative moves:                        {result['relative_moves']}")
    print(f"max move:                              {result['max_move']:.1f}")
    print(f"11850 -> 0 legal path:                 {result['descent_path_to_zero']}")
    print(f"updates to zero at max negative move:  {updates_to_zero}")
    print(f"time at Ts=500 ms:                     {seconds_to_zero_at_max_negative_move:.1f} s")
    print(f"V3E high-DAC samples above SP:         {len(high_dac_above_sp)}")
    print(f"with legal V3F downward action:        {downward_available}")
    print(f"availability fraction:                 {100.0*availability_fraction:.1f}%")

    if result["candidate_count_interior"] != 13:
        raise RuntimeError("Interior V3F candidate count is not 13.")
    if path[-1] != 0.0:
        raise RuntimeError("V3F action graph did not reach zero.")
    if availability_fraction < 0.999999:
        raise RuntimeError(
            "V3F does not provide a legal downward action for all high-DAC samples above SP."
        )

    print()
    print("V3F CONNECTED ACTION-SPACE TOPOLOGY: PASSED")
    print(f"RESULT: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
