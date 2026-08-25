from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import msvcrt
import statistics
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# CHECKPOINTED EXECUTION CONTRACT
# ---------------------------------------------------------------------------

REMAINING_DAC_POINTS = (11650, 11700, 11750, 11800, 11850, 11900)

SAMPLE_S = 0.1

TARGET_TOLERANCE_DAC = 5.0
TARGET_CONFIRM_SAMPLES = 5
TARGET_ACQUISITION_TIMEOUT_S = 30.0

CONSTANT_TARGET_HOLD_S = 45.0

MINIMUM_ZERO_RECOVERY_S = 30.0
STABLE_REBASELINE_WINDOW_S = 20.0
STABLE_MAX_ABS_SLOPE_RAW_PER_S = 1.0
STABLE_MAX_MEDIAN9_RANGE_RAW = 30.0
MAXIMUM_PHYSICAL_HEIGHT_BEFORE_NEXT_POINT_CM = 1.0

MAX_INSTANT_RAW = 1100.0
MAX_MEDIAN9_RAW = 1100.0
MAX_POSITIVE_MEDIAN_RATE_RAW_PER_S = 180.0
MAX_DAC = 12000.0
ACTIVE_PHYSICAL_ABORT_CM = 5.0

FINAL_ZERO_CONFIRM_S = 10.0

TRANSPORT_DELAY_S = 9.0
IDENTIFIED_TAU_S = 4.75

GW_ENDPOINT = "opc.tcp://127.0.0.1:4841"
GW_URI = "urn:br-4diac-gateway"
PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"

PLC_NODE_IDS = {
    "Nivel":           "ns=6;s=::Program:Nivel",
    "WatchdogHealthy": "ns=6;s=::Program:WatchdogHealthy",
    "WatchdogTripped": "ns=6;s=::Program:WatchdogTripped",
    "Enable":          "ns=6;s=::Program:Enable",
    "DAC":             "ns=6;s=::Program:DAC",
    "AppliedEnable":   "ns=6;s=::Program:AppliedEnable",
    "AppliedDAC":      "ns=6;s=::Program:AppliedDAC",
}


class ExperimentAbort(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Protected resume executor for the remaining local dead-zone "
            "identification points 11650..11900."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="Print contract only; no network access.")
    mode.add_argument("--run", action="store_true", help="Execute the protected real-lab experiment.")
    parser.add_argument("--evidence-dir", type=Path)
    return parser


def print_plan() -> int:
    post_delay = CONSTANT_TARGET_HOLD_S - TRANSPORT_DELAY_S
    post_delay_tau = post_delay / IDENTIFIED_TAU_S

    print("MPC LOCAL DEAD-ZONE RESUME EXECUTOR PLAN")
    print("========================================")
    print("NETWORK ACCESS: NO")
    print("PLC ACCESS: NO")
    print("GATEWAY ACCESS: NO")
    print("OPC UA WRITES: NO")
    print("REAL ACTUATION: NO")
    print("MODE: PLAN ONLY")
    print()
    print(f"remaining DAC points:             {list(REMAINING_DAC_POINTS)}")
    print(f"sample period:                    {SAMPLE_S:.3f} s")
    print(f"target tolerance:                 +/-{TARGET_TOLERANCE_DAC:.0f} DAC")
    print(f"target confirmations:             {TARGET_CONFIRM_SAMPLES}")
    print(f"target acquisition timeout:       {TARGET_ACQUISITION_TIMEOUT_S:.1f} s")
    print(f"constant-target hold:             {CONSTANT_TARGET_HOLD_S:.1f} s")
    print(f"post-delay data if completed:     {post_delay:.1f} s")
    print(f"post-delay / tau:                 {post_delay_tau:.2f}x")
    print()
    print(f"minimum zero recovery:            {MINIMUM_ZERO_RECOVERY_S:.1f} s")
    print(f"stable rebaseline window:         {STABLE_REBASELINE_WINDOW_S:.1f} s")
    print(f"stable abs slope limit:           {STABLE_MAX_ABS_SLOPE_RAW_PER_S:.1f} raw/s")
    print(f"stable Median9 range limit:       {STABLE_MAX_MEDIAN9_RANGE_RAW:.1f} raw")
    print(f"physical level before next point: <= {MAXIMUM_PHYSICAL_HEIGHT_BEFORE_NEXT_POINT_CM:.1f} cm")
    print()
    print(f"instant raw abort:                {MAX_INSTANT_RAW:.0f}")
    print(f"Median9 abort:                    {MAX_MEDIAN9_RAW:.0f}")
    print(f"positive rate abort:              {MAX_POSITIVE_MEDIAN_RATE_RAW_PER_S:.0f} raw/s")
    print(f"DAC hard maximum:                 {MAX_DAC:.0f}")
    print(f"active physical abort:            {ACTIVE_PHYSICAL_ABORT_CM:.1f} cm")
    print()
    print("11600 automatic repetition:       NO")
    print("45-s hold includes actuator ramp: NO")
    print("return to first numeric baseline: NO")
    print("per-point local rebaseline:       YES")
    print("Delta Median9 logging:            YES")
    return 0


def operator_abort_requested() -> bool:
    if not msvcrt.kbhit():
        return False
    return msvcrt.getwch().lower() == "q"


def linear_slope(samples: deque[tuple[float, float]]) -> float:
    if len(samples) < 2:
        return 0.0
    xs = [x for x, _ in samples]
    ys = [y for _, y in samples]
    xm = statistics.fmean(xs)
    ym = statistics.fmean(ys)
    den = sum((x - xm) ** 2 for x in xs)
    if den <= 0.0:
        return 0.0
    return sum((x - xm) * (y - ym) for x, y in samples) / den


def trim_history(history: deque[tuple[float, float]], now: float, span_s: float) -> None:
    while history and now - history[0][0] > span_s:
        history.popleft()


async def run_real(evidence_dir: Path) -> int:
    # Import asyncua only in --run mode. --plan mode is guaranteed not to touch
    # OPC UA or require runtime communication dependencies.
    from asyncua import Client, ua

    # The PowerShell wrapper may pre-create this directory so it can redirect
    # gateway stdout/stderr into the same run folder. Accept that directory,
    # but never overwrite evidence owned by this runner.
    evidence_dir.mkdir(parents=True, exist_ok=True)

    csv_path = evidence_dir / "local-deadzone-resume-monitor.csv"
    summary_path = evidence_dir / "run-summary.json"
    physical_path = evidence_dir / "physical-observations.txt"

    runner_owned_paths = (csv_path, summary_path, physical_path)
    existing_runner_evidence = [p for p in runner_owned_paths if p.exists()]
    if existing_runner_evidence:
        joined = ", ".join(str(p) for p in existing_runner_evidence)
        raise FileExistsError(
            "Refusing to overwrite existing runner evidence: " + joined
        )

    fieldnames = [
        "elapsed_s",
        "phase",
        "point_index",
        "target_dac",
        "local_baseline_raw",
        "nivel_raw",
        "median9_raw",
        "delta_median9_raw",
        "positive_median_rate_raw_per_s",
        "signed_stability_slope_raw_per_s",
        "enable",
        "dac",
        "applied_enable",
        "applied_dac",
        "watchdog_healthy",
        "watchdog_tripped",
    ]

    levels: deque[float] = deque(maxlen=9)
    rate_history: deque[tuple[float, float]] = deque()
    stable_history: deque[tuple[float, float]] = deque()

    run_t0 = time.monotonic()

    summary: dict[str, Any] = {
        "classification": "INCOMPLETE",
        "run_started": datetime.now().isoformat(timespec="seconds"),
        "remaining_dac_points": list(REMAINING_DAC_POINTS),
        "points": [],
        "initial_rebaseline": None,
        "stop_reason": None,
        "final_zero_verified": False,
    }

    async def write_value(node, value, variant_type) -> None:
        await node.write_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(ua.Variant(value, variant_type)),
        )

    async with Client(GW_ENDPOINT, timeout=5.0) as gw, Client(PLC_ENDPOINT, timeout=5.0) as plc:
        ns = await gw.get_namespace_index(GW_URI)

        gw_nodes = {
            "Enable": gw.get_node(f"ns={ns};s=Enable"),
            "DAC": gw.get_node(f"ns={ns};s=DAC"),
        }
        plc_nodes = {name: plc.get_node(node_id) for name, node_id in PLC_NODE_IDS.items()}

        async def read_snapshot() -> dict[str, Any]:
            return {
                "raw": float(await plc_nodes["Nivel"].read_value()),
                "healthy": bool(await plc_nodes["WatchdogHealthy"].read_value()),
                "tripped": bool(await plc_nodes["WatchdogTripped"].read_value()),
                "enable": bool(await plc_nodes["Enable"].read_value()),
                "dac": float(await plc_nodes["DAC"].read_value()),
                "applied_enable": bool(await plc_nodes["AppliedEnable"].read_value()),
                "applied_dac": float(await plc_nodes["AppliedDAC"].read_value()),
            }

        async def force_zero() -> None:
            # Gateway writes first, then PLC writes as independent fail-safe.
            writes = (
                (gw_nodes["Enable"], False, ua.VariantType.Boolean),
                (gw_nodes["DAC"], 0, ua.VariantType.Int16),
                (plc_nodes["Enable"], False, ua.VariantType.Boolean),
                (plc_nodes["DAC"], 0, ua.VariantType.Int16),
            )
            warnings = []
            for node, value, variant_type in writes:
                try:
                    await write_value(node, value, variant_type)
                except Exception as exc:
                    warnings.append(str(exc))
            if warnings:
                print("Safe-zero write warning(s):")
                for warning in warnings:
                    print("  " + warning)

        async def verify_zero(timeout_s: float = 12.0) -> dict[str, Any]:
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                s = await read_snapshot()
                if (
                    not s["enable"]
                    and abs(s["dac"]) <= 0.1
                    and not s["applied_enable"]
                    and abs(s["applied_dac"]) <= 0.1
                ):
                    return s
                await asyncio.sleep(0.2)
            raise ExperimentAbort("ZERO_OUTPUT_VERIFICATION_FAILED")

        def safety_check(snapshot: dict[str, Any], median9: float, positive_rate: float) -> None:
            if not snapshot["healthy"] or snapshot["tripped"]:
                raise ExperimentAbort("WATCHDOG_ABORT")
            if snapshot["raw"] >= MAX_INSTANT_RAW:
                raise ExperimentAbort("INSTANT_RAW_ABORT")
            if median9 >= MAX_MEDIAN9_RAW:
                raise ExperimentAbort("MEDIAN9_ABORT")
            if positive_rate >= MAX_POSITIVE_MEDIAN_RATE_RAW_PER_S:
                raise ExperimentAbort("POSITIVE_MEDIAN_RATE_ABORT")
            if snapshot["dac"] > MAX_DAC or snapshot["applied_dac"] > MAX_DAC:
                raise ExperimentAbort("DAC_LIMIT_ABORT")

        def update_signal_state(snapshot: dict[str, Any], now: float) -> tuple[float, float]:
            levels.append(snapshot["raw"])
            median9 = float(statistics.median(levels))
            rate_history.append((now, median9))
            trim_history(rate_history, now, 1.0)
            positive_rate = max(0.0, linear_slope(rate_history))
            return median9, positive_rate

        def log_row(
            writer: csv.DictWriter,
            *,
            now: float,
            phase: str,
            point_index: int,
            target_dac: int,
            local_baseline: float | None,
            snapshot: dict[str, Any],
            median9: float,
            positive_rate: float,
            signed_slope: float | None = None,
        ) -> None:
            delta = None if local_baseline is None else median9 - local_baseline
            writer.writerow({
                "elapsed_s": f"{now - run_t0:.3f}",
                "phase": phase,
                "point_index": point_index,
                "target_dac": target_dac,
                "local_baseline_raw": "" if local_baseline is None else f"{local_baseline:.3f}",
                "nivel_raw": f"{snapshot['raw']:.3f}",
                "median9_raw": f"{median9:.3f}",
                "delta_median9_raw": "" if delta is None else f"{delta:.3f}",
                "positive_median_rate_raw_per_s": f"{positive_rate:.3f}",
                "signed_stability_slope_raw_per_s": "" if signed_slope is None else f"{signed_slope:.3f}",
                "enable": snapshot["enable"],
                "dac": f"{snapshot['dac']:.3f}",
                "applied_enable": snapshot["applied_enable"],
                "applied_dac": f"{snapshot['applied_dac']:.3f}",
                "watchdog_healthy": snapshot["healthy"],
                "watchdog_tripped": snapshot["tripped"],
            })

        async def establish_zero_rebaseline(
            writer: csv.DictWriter,
            *,
            phase: str,
            point_index: int,
            prior_target: int,
        ) -> tuple[float, float]:
            await force_zero()
            await verify_zero()

            start = time.monotonic()
            stable_history.clear()
            accepted_window_values: list[float] = []
            last_print = -1.0

            while True:
                now = time.monotonic()

                if operator_abort_requested():
                    raise ExperimentAbort("OPERATOR_ABORT_DURING_REBASELINE")

                s = await read_snapshot()
                if (
                    s["enable"]
                    or abs(s["dac"]) > 0.1
                    or s["applied_enable"]
                    or abs(s["applied_dac"]) > 0.1
                ):
                    raise ExperimentAbort("NONZERO_OUTPUT_DURING_REBASELINE")

                median9, positive_rate = update_signal_state(s, now)

                if not s["healthy"] or s["tripped"]:
                    raise ExperimentAbort("WATCHDOG_ABORT_DURING_REBASELINE")

                stable_history.append((now, median9))
                trim_history(stable_history, now, STABLE_REBASELINE_WINDOW_S)

                signed_slope = linear_slope(stable_history)
                stable_values = [value for _, value in stable_history]
                stable_range = (
                    max(stable_values) - min(stable_values)
                    if stable_values
                    else math.inf
                )

                log_row(
                    writer,
                    now=now,
                    phase=phase,
                    point_index=point_index,
                    target_dac=0,
                    local_baseline=None,
                    snapshot=s,
                    median9=median9,
                    positive_rate=positive_rate,
                    signed_slope=signed_slope,
                )

                elapsed = now - start
                window_ready = (
                    len(stable_history) >= 2
                    and stable_history[-1][0] - stable_history[0][0]
                    >= STABLE_REBASELINE_WINDOW_S - 0.25
                )

                stable = (
                    elapsed >= MINIMUM_ZERO_RECOVERY_S
                    and window_ready
                    and abs(signed_slope) <= STABLE_MAX_ABS_SLOPE_RAW_PER_S
                    and stable_range <= STABLE_MAX_MEDIAN9_RANGE_RAW
                )

                if elapsed - last_print >= 1.0:
                    print(
                        f"REBASELINE {elapsed:6.1f}s | raw={s['raw']:7.1f} | "
                        f"Med9={median9:7.1f} | slope={signed_slope:+6.2f} | "
                        f"range={stable_range:5.1f}"
                    )
                    last_print = elapsed

                if stable:
                    accepted_window_values = stable_values
                    local_baseline = float(statistics.median(accepted_window_values))
                    return local_baseline, elapsed

                await asyncio.sleep(SAMPLE_S)

        await force_zero()
        await verify_zero()

        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()

            print()
            print("INITIAL STABLE ZERO-OUTPUT REBASELINE")
            print("=====================================")
            print("Press Q for operator abort.")
            initial_baseline, initial_recovery_s = await establish_zero_rebaseline(
                writer,
                phase="INITIAL_REBASELINE",
                point_index=0,
                prior_target=0,
            )
            fh.flush()

            print()
            print(f"Initial local baseline accepted: {initial_baseline:.1f} raw")
            initial_physical_text = input(
                "Current physical water height (cm, must be <=1 cm): "
            ).strip().lower().replace("cm", "").strip().replace(",", ".")

            try:
                initial_physical_cm = float(initial_physical_text)
            except ValueError as exc:
                raise ExperimentAbort("INVALID_INITIAL_PHYSICAL_HEIGHT") from exc

            if not (0.0 <= initial_physical_cm <= MAXIMUM_PHYSICAL_HEIGHT_BEFORE_NEXT_POINT_CM):
                raise ExperimentAbort("INITIAL_PHYSICAL_HEIGHT_ABOVE_1CM")

            summary["initial_rebaseline"] = {
                "baseline_raw": initial_baseline,
                "duration_s": initial_recovery_s,
                "physical_cm": initial_physical_cm,
            }

            local_baseline = initial_baseline

            for point_index, target_dac in enumerate(REMAINING_DAC_POINTS, start=1):
                print()
                print("=" * 90)
                print(f"POINT {point_index}/{len(REMAINING_DAC_POINTS)} - DAC {target_dac}")
                print("=" * 90)
                print(f"Current local baseline: {local_baseline:.1f} raw")
                print("Hold clock starts ONLY after target acquisition gate.")
                print("Press Q for immediate operator abort.")
                print()

                token = input(
                    f"Type APPLY_{target_dac} only if physical state is safe and ruler is visible: "
                ).strip()

                if token != f"APPLY_{target_dac}":
                    summary["stop_reason"] = f"POINT_{target_dac}_NOT_AUTHORIZED"
                    break

                # -----------------------------------------------------------
                # TARGET ACQUISITION
                # -----------------------------------------------------------
                await write_value(gw_nodes["DAC"], int(target_dac), ua.VariantType.Int16)
                await write_value(gw_nodes["Enable"], True, ua.VariantType.Boolean)

                acquisition_start = time.monotonic()
                confirmations = 0
                acquisition_rows = 0

                print("TARGET ACQUISITION")
                print("------------------")

                while True:
                    now = time.monotonic()
                    if operator_abort_requested():
                        raise ExperimentAbort(f"OPERATOR_ABORT_ACQUIRE_{target_dac}")

                    s = await read_snapshot()
                    median9, positive_rate = update_signal_state(s, now)
                    safety_check(s, median9, positive_rate)

                    in_target = abs(s["applied_dac"] - target_dac) <= TARGET_TOLERANCE_DAC
                    confirmations = confirmations + 1 if in_target else 0
                    acquisition_rows += 1

                    log_row(
                        writer,
                        now=now,
                        phase="ACQUIRE",
                        point_index=point_index,
                        target_dac=target_dac,
                        local_baseline=local_baseline,
                        snapshot=s,
                        median9=median9,
                        positive_rate=positive_rate,
                    )
                    fh.flush()

                    elapsed = now - acquisition_start
                    print(
                        f"ACQUIRE {elapsed:5.1f}s | Applied={s['applied_dac']:7.1f} | "
                        f"target={target_dac} | confirmations={confirmations}/{TARGET_CONFIRM_SAMPLES} | "
                        f"Med9={median9:7.1f} | Delta={median9-local_baseline:+7.1f}"
                    )

                    if confirmations >= TARGET_CONFIRM_SAMPLES:
                        acquisition_elapsed = elapsed
                        break

                    if elapsed >= TARGET_ACQUISITION_TIMEOUT_S:
                        raise ExperimentAbort(f"TARGET_ACQUISITION_TIMEOUT_{target_dac}")

                    await asyncio.sleep(SAMPLE_S)

                print()
                print(
                    f"Target {target_dac} acquired after {acquisition_elapsed:.2f} s. "
                    f"Starting full {CONSTANT_TARGET_HOLD_S:.1f} s constant-target hold NOW."
                )

                # -----------------------------------------------------------
                # CONSTANT-TARGET HOLD
                # -----------------------------------------------------------
                hold_start = time.monotonic()
                hold_rows = 0
                hold_raw: list[float] = []
                hold_med: list[float] = []
                hold_delta: list[float] = []
                hold_applied: list[float] = []
                last_print = -1.0

                try:
                    while time.monotonic() - hold_start < CONSTANT_TARGET_HOLD_S:
                        now = time.monotonic()

                        if operator_abort_requested():
                            raise ExperimentAbort(f"OPERATOR_ABORT_HOLD_{target_dac}")

                        s = await read_snapshot()
                        median9, positive_rate = update_signal_state(s, now)
                        safety_check(s, median9, positive_rate)

                        if abs(s["applied_dac"] - target_dac) > TARGET_TOLERANCE_DAC:
                            raise ExperimentAbort(f"APPLIED_DAC_LEFT_TARGET_{target_dac}")

                        delta = median9 - local_baseline

                        log_row(
                            writer,
                            now=now,
                            phase="HOLD",
                            point_index=point_index,
                            target_dac=target_dac,
                            local_baseline=local_baseline,
                            snapshot=s,
                            median9=median9,
                            positive_rate=positive_rate,
                        )
                        fh.flush()

                        hold_rows += 1
                        hold_raw.append(s["raw"])
                        hold_med.append(median9)
                        hold_delta.append(delta)
                        hold_applied.append(s["applied_dac"])

                        elapsed = now - hold_start
                        if elapsed - last_print >= 0.5:
                            print(
                                f"HOLD {elapsed:5.1f}s | raw={s['raw']:7.1f} | "
                                f"Med9={median9:7.1f} | Delta={delta:+7.1f} | "
                                f"Rate+={positive_rate:6.1f} | Applied={s['applied_dac']:7.1f}"
                            )
                            last_print = elapsed

                        await asyncio.sleep(SAMPLE_S)

                except Exception:
                    await force_zero()
                    await verify_zero()
                    raise

                hold_duration = time.monotonic() - hold_start

                await force_zero()
                await verify_zero()

                print()
                print("CONSTANT-TARGET HOLD COMPLETE")
                print(f"Target DAC: {target_dac}")
                print(f"Hold duration: {hold_duration:.2f} s")
                print(f"Samples: {hold_rows}")
                print(f"Median9 min/max: {min(hold_med):.1f} .. {max(hold_med):.1f}")
                print(f"Delta Median9 min/max: {min(hold_delta):+.1f} .. {max(hold_delta):+.1f}")

                max_physical_text = input(
                    "Maximum physical height observed during this HOLD (cm): "
                ).strip().lower().replace("cm", "").strip().replace(",", ".")

                try:
                    max_physical_cm = float(max_physical_text)
                except ValueError as exc:
                    raise ExperimentAbort("INVALID_ACTIVE_PHYSICAL_HEIGHT") from exc

                if not (0.0 <= max_physical_cm <= 25.0):
                    raise ExperimentAbort("ACTIVE_PHYSICAL_HEIGHT_OUT_OF_RANGE")

                point_result: dict[str, Any] = {
                    "index": point_index,
                    "target_dac": target_dac,
                    "local_baseline_before_raw": local_baseline,
                    "target_acquisition_s": acquisition_elapsed,
                    "target_acquisition_samples": acquisition_rows,
                    "constant_target_hold_s": hold_duration,
                    "hold_samples": hold_rows,
                    "median9_min_raw": min(hold_med),
                    "median9_max_raw": max(hold_med),
                    "delta_median9_min_raw": min(hold_delta),
                    "delta_median9_max_raw": max(hold_delta),
                    "applied_dac_median": statistics.median(hold_applied),
                    "maximum_physical_cm": max_physical_cm,
                }
                summary["points"].append(point_result)

                if max_physical_cm >= ACTIVE_PHYSICAL_ABORT_CM:
                    summary["stop_reason"] = f"PHYSICAL_ABORT_AFTER_{target_dac}"
                    break

                # -----------------------------------------------------------
                # ZERO-OUTPUT RECOVERY / LOCAL REBASELINE
                # -----------------------------------------------------------
                print()
                print("ZERO-OUTPUT RECOVERY / LOCAL REBASELINE")
                print("---------------------------------------")
                print(f"Minimum zero time: {MINIMUM_ZERO_RECOVERY_S:.1f} s")
                print(f"Stable window: {STABLE_REBASELINE_WINDOW_S:.1f} s")
                print(f"|slope| <= {STABLE_MAX_ABS_SLOPE_RAW_PER_S:.1f} raw/s")
                print(f"Median9 range <= {STABLE_MAX_MEDIAN9_RANGE_RAW:.1f} raw")

                next_baseline, recovery_s = await establish_zero_rebaseline(
                    writer,
                    phase="RECOVERY_REBASELINE",
                    point_index=point_index,
                    prior_target=target_dac,
                )
                fh.flush()

                print()
                print(f"Stable local baseline accepted: {next_baseline:.1f} raw")

                physical_recovery_text = input(
                    "Current physical water height after recovery (cm, must be <=1 cm to continue): "
                ).strip().lower().replace("cm", "").strip().replace(",", ".")

                try:
                    physical_recovery_cm = float(physical_recovery_text)
                except ValueError as exc:
                    raise ExperimentAbort("INVALID_RECOVERY_PHYSICAL_HEIGHT") from exc

                point_result["recovery_s"] = recovery_s
                point_result["local_baseline_after_raw"] = next_baseline
                point_result["physical_after_recovery_cm"] = physical_recovery_cm

                if not (
                    0.0
                    <= physical_recovery_cm
                    <= MAXIMUM_PHYSICAL_HEIGHT_BEFORE_NEXT_POINT_CM
                ):
                    summary["stop_reason"] = f"RECOVERY_PHYSICAL_LEVEL_ABOVE_1CM_AFTER_{target_dac}"
                    break

                local_baseline = next_baseline

            await force_zero()
            await verify_zero()

            print()
            print(f"FINAL ZERO CONFIRMATION: {FINAL_ZERO_CONFIRM_S:.1f} s")
            final_start = time.monotonic()

            while time.monotonic() - final_start < FINAL_ZERO_CONFIRM_S:
                s = await read_snapshot()
                if (
                    s["enable"]
                    or abs(s["dac"]) > 0.1
                    or s["applied_enable"]
                    or abs(s["applied_dac"]) > 0.1
                ):
                    raise ExperimentAbort("FINAL_ZERO_HOLD_VIOLATION")
                if not s["healthy"] or s["tripped"]:
                    raise ExperimentAbort("FINAL_WATCHDOG_ABORT")
                await asyncio.sleep(0.2)

            summary["final_zero_verified"] = True

            if summary["stop_reason"] is None:
                if len(summary["points"]) == len(REMAINING_DAC_POINTS):
                    summary["classification"] = "COMPLETED_REMAINING_LOCAL_DEADZONE_IDENTIFICATION"
                    summary["stop_reason"] = "ALL_REMAINING_POINTS_COMPLETE"
                else:
                    summary["classification"] = "PARTIAL_REMAINING_LOCAL_DEADZONE_IDENTIFICATION"
                    summary["stop_reason"] = "STOPPED_BEFORE_ALL_POINTS"
            else:
                summary["classification"] = "BOUNDED_PARTIAL_REMAINING_LOCAL_DEADZONE_IDENTIFICATION"

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    physical_lines = [
        "Protected local dead-zone resume experiment",
        f"Run started: {summary['run_started']}",
        f"Classification: {summary['classification']}",
        f"Stop reason: {summary['stop_reason']}",
        "",
    ]
    for p in summary["points"]:
        physical_lines.extend([
            f"DAC {p['target_dac']}:",
            f"  maximum physical during hold: {p['maximum_physical_cm']} cm",
            f"  physical after recovery: {p.get('physical_after_recovery_cm')} cm",
            "",
        ])
    physical_lines.append(f"Final zero verified: {summary['final_zero_verified']}")
    physical_path.write_text("\n".join(physical_lines) + "\n", encoding="utf-8")

    print()
    print("PROTECTED RESUME IDENTIFICATION FINISHED")
    print("========================================")
    print(f"Classification: {summary['classification']}")
    print(f"Stop reason: {summary['stop_reason']}")
    print(f"Completed points: {len(summary['points'])}/{len(REMAINING_DAC_POINTS)}")
    print(f"Final zero verified: {summary['final_zero_verified']}")
    print(f"CSV:      {csv_path}")
    print(f"SUMMARY:  {summary_path}")
    print(f"PHYSICAL: {physical_path}")

    return 0


async def run_with_final_zero_guard(evidence_dir: Path) -> int:
    try:
        return await run_real(evidence_dir)
    except Exception as exc:
        print()
        print(f"EXECUTOR ABORTED: {type(exc).__name__}: {exc}")
        print("The wrapper must preserve the evidence directory and must not auto-retry.")
        raise


def main() -> int:
    args = build_parser().parse_args()

    if args.plan:
        return print_plan()

    if args.evidence_dir is None:
        raise SystemExit("--run requires --evidence-dir")

    return asyncio.run(run_with_final_zero_guard(args.evidence_dir))


if __name__ == "__main__":
    raise SystemExit(main())
