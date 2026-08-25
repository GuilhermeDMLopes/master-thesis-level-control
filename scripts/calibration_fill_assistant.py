from __future__ import annotations

import argparse
import asyncio
import csv
import statistics
import time
from collections import deque
from datetime import datetime
from pathlib import Path

PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
GATEWAY_URI = "urn:br-4diac-gateway"
TOKEN = "CALIBRATION_FILL_READY"

PLC_IDS = {
    "Nivel": "ns=6;s=::Program:Nivel",
    "Enable": "ns=6;s=::Program:Enable",
    "DAC": "ns=6;s=::Program:DAC",
    "SafetyReset": "ns=6;s=::Program:SafetyReset",
    "WatchdogHealthy": "ns=6;s=::Program:WatchdogHealthy",
    "WatchdogTripped": "ns=6;s=::Program:WatchdogTripped",
    "AppliedEnable": "ns=6;s=::Program:AppliedEnable",
    "AppliedDAC": "ns=6;s=::Program:AppliedDAC",
}

ZERO_VERIFY_SAMPLES = 5
ZERO_VERIFY_TIMEOUT_S = 20.0
SOFT_STOP_WINDOW = 9
SOFT_STOP_CONSECUTIVE = 3


def build_parser():
    p = argparse.ArgumentParser(
        description=(
            "Human-in-the-loop fill assistant V3 for static level calibration. "
            "The raw soft stop uses a rolling median rather than one noisy sample."
        )
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    p.add_argument("--target-dac", type=int, required=True)
    p.add_argument("--max-raw", type=int, required=True)
    p.add_argument("--target-height-cm", type=float, default=5.0)
    p.add_argument("--hold-s", type=float, default=1.0)
    p.add_argument("--settle-s", type=float, default=10.0)
    p.add_argument("--sample-s", type=float, default=0.1)
    p.add_argument("--timeout-s", type=float, default=20.0)
    p.add_argument("--output-root", type=Path, default=Path("data/raw"))
    return p


def validate(a):
    if not 1 <= a.target_dac <= 12000:
        raise ValueError("target DAC must be between 1 and 12000")
    if a.max_raw <= 0:
        raise ValueError("max raw must be positive")
    if a.target_height_cm <= 0:
        raise ValueError("target height must be positive")
    if a.hold_s < 0:
        raise ValueError("hold time must not be negative")
    if a.settle_s <= 0 or a.sample_s <= 0 or a.timeout_s <= 0:
        raise ValueError("timing values are invalid")


def print_plan(a):
    print("CALIBRATION FILL ASSISTANT PLAN V3")
    print("==================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"Target DAC per pulse: {a.target_dac}")
    print(f"Rolling-median soft stop: {a.max_raw} raw")
    print(f"Soft-stop window: {SOFT_STOP_WINDOW} samples")
    print(f"Soft-stop confirmations: {SOFT_STOP_CONSECUTIVE}")
    print(f"Target physical height: {a.target_height_cm:.2f} cm")
    print(f"Hold after target DAC: {a.hold_s:.2f} s")
    print(f"Pump-off settling time: {a.settle_s:.2f} s")
    print(f"Complete zero-state timeout: {ZERO_VERIFY_TIMEOUT_S:.1f} s")
    print()
    print("One pulse is applied only after ENTER.")
    print("The pump is then forced off and complete zero state is verified.")
    print("You measure the physical height before another pulse is possible.")
    print(f"Confirmation token: {TOKEN}")


def zero_state(s):
    return (
        s["Enable"] is False
        and int(s["DAC"]) == 0
        and s["AppliedEnable"] is False
        and int(s["AppliedDAC"]) == 0
    )


def healthy(s):
    return (
        s["SafetyReset"] is False
        and s["WatchdogHealthy"] is True
        and s["WatchdogTripped"] is False
    )


def state_text(s):
    return (
        f"Enable={bool(s['Enable'])} "
        f"DAC={int(s['DAC'])} "
        f"AppliedEnable={bool(s['AppliedEnable'])} "
        f"AppliedDAC={int(s['AppliedDAC'])} "
        f"Healthy={bool(s['WatchdogHealthy'])} "
        f"Tripped={bool(s['WatchdogTripped'])}"
    )


async def execute(a):
    from asyncua import Client, ua

    answer = input(
        "Type CALIBRATION_FILL_READY only if: physical stop accessible, "
        "FORTE stopped, gateway running, tank below 5 cm, and trena ready: "
    ).strip()
    if answer != TOKEN:
        raise RuntimeError("calibration fill was not confirmed")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = a.output_root / f"calibration-fill-{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    samples_path = folder / "samples.csv"
    points_path = folder / "points.csv"

    async with Client(PLC_ENDPOINT, timeout=5.0) as plc:
        async with Client(GATEWAY_ENDPOINT, timeout=5.0) as gw:
            ns = await gw.get_namespace_index(GATEWAY_URI)
            enable_node = gw.get_node(ua.NodeId("Enable", ns))
            dac_node = gw.get_node(ua.NodeId("DAC", ns))
            plc_nodes = {
                name: plc.get_node(node_id)
                for name, node_id in PLC_IDS.items()
            }

            async def read_state():
                return {
                    name: await node.read_value()
                    for name, node in plc_nodes.items()
                }

            async def write_only(node, value, variant_type):
                await node.write_attribute(
                    ua.AttributeIds.Value,
                    ua.DataValue(ua.Variant(value, variant_type)),
                )

            async def force_zero():
                await write_only(
                    enable_node,
                    False,
                    ua.VariantType.Boolean,
                )
                await write_only(
                    dac_node,
                    0,
                    ua.VariantType.Int16,
                )

                stable = 0
                deadline = time.monotonic() + ZERO_VERIFY_TIMEOUT_S
                last_print = 0.0

                while time.monotonic() < deadline:
                    s = await read_state()
                    now = time.monotonic()

                    stable = stable + 1 if zero_state(s) else 0

                    if now - last_print >= 0.5:
                        print("Zero-state check: " + state_text(s))
                        last_print = now

                    if stable >= ZERO_VERIFY_SAMPLES:
                        print(
                            "Complete command + applied zero-output state: PASSED "
                            f"({ZERO_VERIFY_SAMPLES} consecutive samples)"
                        )
                        return

                    await asyncio.sleep(0.2)

                raise RuntimeError(
                    "complete zero-state verification timed out: "
                    + state_text(await read_state())
                )

            initial = await read_state()
            if not healthy(initial):
                raise RuntimeError(
                    "watchdog is not healthy before calibration: "
                    + state_text(initial)
                )
            if not zero_state(initial):
                raise RuntimeError(
                    "calibration must start at complete zero state: "
                    + state_text(initial)
                )

            with samples_path.open(
                "w", newline="", encoding="utf-8"
            ) as sf, points_path.open(
                "w", newline="", encoding="utf-8"
            ) as pf:
                sw = csv.writer(sf, delimiter=";")
                pw = csv.writer(pf, delimiter=";")

                sw.writerow([
                    "timestamp", "cycle", "phase",
                    "level_raw", "level_median9",
                    "watchdog_healthy", "watchdog_tripped",
                    "enable", "dac", "applied_enable", "applied_dac",
                ])
                pw.writerow([
                    "cycle", "height_cm",
                    "raw_min", "raw_max", "raw_median", "raw_mean",
                    "raw_peak_to_peak", "target_dac", "soft_stop_raw",
                ])

                cycle = 0
                final_zero_done = False

                try:
                    while True:
                        s = await read_state()
                        current = int(s["Nivel"])
                        print()
                        print(
                            f"Current raw={current} | target DAC={a.target_dac} | "
                            f"median soft stop={a.max_raw}"
                        )

                        command = input(
                            "Press ENTER for ONE pulse, or type Q to finish: "
                        ).strip().upper()
                        if command == "Q":
                            break
                        if command:
                            print("Unknown command. No pulse applied.")
                            continue

                        cycle += 1
                        print(f"Cycle {cycle}: controlled pulse starting...")

                        await write_only(
                            enable_node,
                            True,
                            ua.VariantType.Boolean,
                        )
                        await write_only(
                            dac_node,
                            a.target_dac,
                            ua.VariantType.Int16,
                        )

                        raw_window = deque(maxlen=SOFT_STOP_WINDOW)
                        soft_stop_hits = 0
                        reached_at = None
                        deadline = time.monotonic() + a.timeout_s
                        last_print = 0.0

                        while True:
                            s = await read_state()
                            now = time.monotonic()
                            raw = int(s["Nivel"])
                            raw_window.append(raw)

                            median9 = (
                                statistics.median(raw_window)
                                if len(raw_window) == SOFT_STOP_WINDOW
                                else None
                            )

                            if median9 is not None and median9 >= a.max_raw:
                                soft_stop_hits += 1
                            else:
                                soft_stop_hits = 0

                            sw.writerow([
                                datetime.now().isoformat(),
                                cycle,
                                "PULSE",
                                raw,
                                "" if median9 is None else median9,
                                bool(s["WatchdogHealthy"]),
                                bool(s["WatchdogTripped"]),
                                bool(s["Enable"]),
                                int(s["DAC"]),
                                bool(s["AppliedEnable"]),
                                int(s["AppliedDAC"]),
                            ])
                            sf.flush()

                            if now - last_print >= 0.25:
                                median_text = (
                                    "n/a"
                                    if median9 is None
                                    else f"{median9:.1f}"
                                )
                                print(
                                    f"Nivel={raw:4d} | Median9={median_text:>6} | "
                                    f"DAC={int(s['DAC']):5d} | "
                                    f"AppliedDAC={int(s['AppliedDAC']):5d}"
                                )
                                last_print = now

                            if not healthy(s):
                                raise RuntimeError(
                                    "watchdog became invalid during pulse: "
                                    + state_text(s)
                                )

                            if soft_stop_hits >= SOFT_STOP_CONSECUTIVE:
                                print(
                                    "Rolling-median calibration soft stop reached. "
                                    "Stopping pulse."
                                )
                                break

                            if int(s["AppliedDAC"]) == a.target_dac:
                                if reached_at is None:
                                    reached_at = now
                                    print(
                                        f"Target AppliedDAC={a.target_dac} reached."
                                    )
                                if now - reached_at >= a.hold_s:
                                    break

                            if now >= deadline:
                                raise RuntimeError(
                                    "DAC target timeout: " + state_text(s)
                                )

                            await asyncio.sleep(a.sample_s)

                        print("Stopping pump...")
                        await force_zero()
                        final_zero_done = True

                        print(f"Settling for {a.settle_s:.1f} s with pump off...")
                        levels = []
                        end = time.monotonic() + a.settle_s

                        while time.monotonic() < end:
                            s = await read_state()

                            if not zero_state(s):
                                raise RuntimeError(
                                    "zero state was lost during settling: "
                                    + state_text(s)
                                )

                            raw = int(s["Nivel"])
                            levels.append(raw)

                            sw.writerow([
                                datetime.now().isoformat(),
                                cycle,
                                "SETTLE",
                                raw,
                                "",
                                bool(s["WatchdogHealthy"]),
                                bool(s["WatchdogTripped"]),
                                bool(s["Enable"]),
                                int(s["DAC"]),
                                bool(s["AppliedEnable"]),
                                int(s["AppliedDAC"]),
                            ])
                            sf.flush()
                            await asyncio.sleep(a.sample_s)

                        rmin = min(levels)
                        rmax = max(levels)
                        rmed = statistics.median(levels)
                        rmean = statistics.fmean(levels)

                        print()
                        print(
                            f"Settled raw: min={rmin}, max={rmax}, "
                            f"median={rmed:.3f}, mean={rmean:.3f}, "
                            f"p-p={rmax-rmin}"
                        )

                        while True:
                            text = input(
                                "Measure height with the trena and type cm "
                                "(example 1.8), or Q to stop: "
                            ).strip()

                            if text.upper() == "Q":
                                height = None
                                break

                            try:
                                height = float(text.replace(",", "."))
                            except ValueError:
                                print("Invalid height.")
                                continue

                            if height < 0:
                                print("Height cannot be negative.")
                                continue
                            break

                        if height is None:
                            break

                        pw.writerow([
                            cycle,
                            height,
                            rmin,
                            rmax,
                            round(rmed, 6),
                            round(rmean, 6),
                            rmax - rmin,
                            a.target_dac,
                            a.max_raw,
                        ])
                        pf.flush()

                        print(
                            f"Recorded calibration point: "
                            f"{height:.2f} cm -> {rmed:.3f} raw"
                        )

                        if height >= a.target_height_cm:
                            print("Physical target reached.")
                            break

                        # Require a fresh operator decision for the next pulse.
                        final_zero_done = False

                finally:
                    # Idempotent: if the previous zero verification already
                    # succeeded, this should return quickly.  The extended
                    # timeout also accommodates the 150-count rate limit.
                    await force_zero()
                    print("Final PLC zero-output verification: PASSED")

    print()
    print("CALIBRATION FILL FINISHED")
    print("=========================")
    print(f"Samples CSV: {samples_path}")
    print(f"Calibration points CSV: {points_path}")
    print("FINAL ZERO OUTPUT: YES")
    return 0


def main():
    p = build_parser()
    a = p.parse_args()

    try:
        validate(a)
    except ValueError as error:
        p.error(str(error))

    if a.plan:
        print_plan(a)
        return 0

    return asyncio.run(execute(a))


if __name__ == "__main__":
    raise SystemExit(main())
