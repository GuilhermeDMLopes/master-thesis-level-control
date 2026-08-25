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
TOKEN = "STEADY_CALIBRATION_READY"

# Temporary engineering envelope for this calibration stage.
# This is NOT the physical actuator limit and does NOT replace
# the PLC's existing 0..32000 bound.
STAGE_DAC_MAX = 16000

# Empirical actuator reference obtained in the laboratory.
# 12000 DAC produced approximately 17.1 Hz on the ACS150 display.
REFERENCE_DAC = 12000.0
REFERENCE_HZ = 17.1

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
ZERO_VERIFY_TIMEOUT_S = 25.0
SOFT_STOP_WINDOW = 9
SOFT_STOP_CONSECUTIVE = 3


def estimated_hz(dac: int) -> float:
    return REFERENCE_HZ * float(dac) / REFERENCE_DAC


def build_parser():
    p = argparse.ArgumentParser(
        description=(
            "Single-plateau calibration assistant V2. "
            "The current stage permits DAC values only up to 16000. "
            "Physical height is measured while the pump is holding "
            "a constant applied DAC."
        )
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")

    p.add_argument("--target-dac", type=int, required=True)
    p.add_argument("--max-raw", type=int, required=True)
    p.add_argument("--hold-s", type=float, required=True)
    p.add_argument("--capture-tail-s", type=float, default=5.0)
    p.add_argument("--sample-s", type=float, default=0.1)
    p.add_argument("--transition-timeout-s", type=float, default=25.0)
    p.add_argument("--output-root", type=Path, default=Path("data/raw"))

    return p


def validate(a):
    if not 1 <= a.target_dac <= STAGE_DAC_MAX:
        raise ValueError(
            f"target DAC must be between 1 and {STAGE_DAC_MAX} "
            "for the current calibration stage"
        )
    if a.max_raw <= 0:
        raise ValueError("max raw must be positive")
    if not 0 < a.hold_s <= 90.0:
        raise ValueError(
            "hold time must be greater than 0 and at most 90 s"
        )
    if not 0 < a.capture_tail_s <= a.hold_s:
        raise ValueError(
            "capture tail must be > 0 and <= hold time"
        )
    if a.sample_s <= 0:
        raise ValueError("sample time must be positive")
    if a.transition_timeout_s <= 0:
        raise ValueError("transition timeout must be positive")


def print_plan(a):
    print("STEADY-STATE CALIBRATION PLAN V2")
    print("================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"Stage DAC ceiling: {STAGE_DAC_MAX}")
    print(f"Target DAC: {a.target_dac}")
    print(
        "Estimated frequency from laboratory reference: "
        f"{estimated_hz(a.target_dac):.2f} Hz"
    )
    print(
        "NOTE: estimated frequency is informational; "
        "the ACS150 display remains authoritative."
    )
    print(f"Rolling-median raw soft stop: {a.max_raw}")
    print(f"Hold at target DAC: {a.hold_s:.2f} s")
    print(f"Calibration capture tail: {a.capture_tail_s:.2f} s")
    print(f"Sampling period: {a.sample_s:.3f} s")
    print(
        f"Zero-output verification timeout: "
        f"{ZERO_VERIFY_TIMEOUT_S:.1f} s"
    )
    print()
    print("During --run:")
    print("1. The system must start at complete zero output.")
    print("2. DAC ramps through the existing limiter.")
    print("3. The target DAC is held for the fixed duration.")
    print("4. The raw rolling-median guard remains active.")
    print("5. Measure height only during the final capture interval.")
    print("6. The pump is stopped automatically.")
    print("7. Complete command + applied zero output is verified.")
    print()
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
        "Type STEADY_CALIBRATION_READY only if: physical stop accessible, "
        "FORTE stopped, gateway running, tank visually safe, trena ready, "
        f"and the {STAGE_DAC_MAX} DAC temporary stage ceiling is understood: "
    ).strip()

    if answer != TOKEN:
        raise RuntimeError(
            "steady-state calibration was not confirmed"
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = (
        a.output_root
        / f"steady-calibration-dac{a.target_dac}-{stamp}"
    )
    folder.mkdir(parents=True, exist_ok=False)

    samples_path = folder / "samples.csv"
    point_path = folder / "calibration-point.csv"

    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as plc:
        async with Client(
            GATEWAY_ENDPOINT,
            timeout=5.0,
        ) as gateway:
            ns = await gateway.get_namespace_index(
                GATEWAY_URI
            )
            enable_node = gateway.get_node(
                ua.NodeId("Enable", ns)
            )
            dac_node = gateway.get_node(
                ua.NodeId("DAC", ns)
            )

            plc_nodes = {
                name: plc.get_node(node_id)
                for name, node_id in PLC_IDS.items()
            }

            async def read_state():
                return {
                    name: await node.read_value()
                    for name, node in plc_nodes.items()
                }

            async def write_only(
                node,
                value,
                variant_type,
            ):
                await node.write_attribute(
                    ua.AttributeIds.Value,
                    ua.DataValue(
                        ua.Variant(
                            value,
                            variant_type,
                        )
                    ),
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
                deadline = (
                    time.monotonic()
                    + ZERO_VERIFY_TIMEOUT_S
                )
                last_print = 0.0

                while time.monotonic() < deadline:
                    state = await read_state()
                    now = time.monotonic()

                    stable = (
                        stable + 1
                        if zero_state(state)
                        else 0
                    )

                    if now - last_print >= 0.5:
                        print(
                            "Zero-state check: "
                            + state_text(state)
                        )
                        last_print = now

                    if stable >= ZERO_VERIFY_SAMPLES:
                        print(
                            "Complete command + applied zero-output "
                            "state: PASSED "
                            f"({ZERO_VERIFY_SAMPLES} consecutive samples)"
                        )
                        return

                    await asyncio.sleep(0.2)

                raise RuntimeError(
                    "zero-state verification timed out: "
                    + state_text(
                        await read_state()
                    )
                )

            initial = await read_state()

            if not healthy(initial):
                raise RuntimeError(
                    "watchdog is not healthy before calibration: "
                    + state_text(initial)
                )

            if not zero_state(initial):
                raise RuntimeError(
                    "calibration must start at complete zero output: "
                    + state_text(initial)
                )

            with samples_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as sf:
                writer = csv.writer(
                    sf,
                    delimiter=";",
                )
                writer.writerow(
                    [
                        "timestamp",
                        "phase",
                        "elapsed_s",
                        "hold_elapsed_s",
                        "level_raw",
                        "median9",
                        "enable",
                        "dac",
                        "applied_enable",
                        "applied_dac",
                        "watchdog_healthy",
                        "watchdog_tripped",
                    ]
                )

                start = time.monotonic()
                raw_window = deque(
                    maxlen=SOFT_STOP_WINDOW
                )
                soft_stop_hits = 0
                capture_samples = []
                hold_completed = False
                soft_stop_triggered = False

                try:
                    print(
                        f"Ramping to DAC={a.target_dac} "
                        f"(~{estimated_hz(a.target_dac):.2f} Hz estimated)..."
                    )

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

                    transition_deadline = (
                        time.monotonic()
                        + a.transition_timeout_s
                    )
                    last_print = 0.0

                    while True:
                        state = await read_state()
                        now = time.monotonic()
                        raw = int(state["Nivel"])
                        raw_window.append(raw)

                        median9 = (
                            statistics.median(
                                raw_window
                            )
                            if len(raw_window)
                            == SOFT_STOP_WINDOW
                            else None
                        )

                        if (
                            median9 is not None
                            and median9 >= a.max_raw
                        ):
                            soft_stop_hits += 1
                        else:
                            soft_stop_hits = 0

                        writer.writerow(
                            [
                                datetime.now().isoformat(),
                                "RAMP",
                                round(
                                    now - start,
                                    6,
                                ),
                                "",
                                raw,
                                (
                                    ""
                                    if median9 is None
                                    else median9
                                ),
                                bool(state["Enable"]),
                                int(state["DAC"]),
                                bool(
                                    state[
                                        "AppliedEnable"
                                    ]
                                ),
                                int(
                                    state[
                                        "AppliedDAC"
                                    ]
                                ),
                                bool(
                                    state[
                                        "WatchdogHealthy"
                                    ]
                                ),
                                bool(
                                    state[
                                        "WatchdogTripped"
                                    ]
                                ),
                            ]
                        )
                        sf.flush()

                        if now - last_print >= 0.25:
                            mtext = (
                                "n/a"
                                if median9 is None
                                else f"{median9:.1f}"
                            )
                            print(
                                f"RAMP | Nivel={raw:4d} | "
                                f"Median9={mtext:>6} | "
                                f"DAC={int(state['DAC']):5d} | "
                                f"AppliedDAC="
                                f"{int(state['AppliedDAC']):5d}"
                            )
                            last_print = now

                        if not healthy(state):
                            raise RuntimeError(
                                "watchdog became invalid during ramp: "
                                + state_text(state)
                            )

                        if (
                            soft_stop_hits
                            >= SOFT_STOP_CONSECUTIVE
                        ):
                            soft_stop_triggered = True
                            print(
                                "Rolling-median raw soft stop "
                                "reached during ramp."
                            )
                            break

                        if (
                            int(state["AppliedDAC"])
                            == a.target_dac
                        ):
                            print(
                                f"Target AppliedDAC="
                                f"{a.target_dac} reached."
                            )
                            break

                        if now >= transition_deadline:
                            raise RuntimeError(
                                "DAC transition timeout: "
                                + state_text(state)
                            )

                        await asyncio.sleep(
                            a.sample_s
                        )

                    if not soft_stop_triggered:
                        hold_start = time.monotonic()
                        capture_start = (
                            hold_start
                            + a.hold_s
                            - a.capture_tail_s
                        )
                        hold_end = (
                            hold_start
                            + a.hold_s
                        )
                        last_print = 0.0
                        raw_window.clear()
                        soft_stop_hits = 0

                        print(
                            f"Holding DAC={a.target_dac} "
                            f"for {a.hold_s:.1f} s."
                        )
                        print(
                            "Observe the ACS150 display and "
                            "measure water height during the "
                            f"FINAL {a.capture_tail_s:.1f} s."
                        )

                        while (
                            time.monotonic()
                            < hold_end
                        ):
                            state = await read_state()
                            now = time.monotonic()
                            raw = int(
                                state["Nivel"]
                            )
                            raw_window.append(raw)

                            median9 = (
                                statistics.median(
                                    raw_window
                                )
                                if len(raw_window)
                                == SOFT_STOP_WINDOW
                                else None
                            )

                            if (
                                median9 is not None
                                and median9
                                >= a.max_raw
                            ):
                                soft_stop_hits += 1
                            else:
                                soft_stop_hits = 0

                            hold_elapsed = (
                                now - hold_start
                            )
                            in_capture = (
                                now >= capture_start
                            )

                            if in_capture:
                                capture_samples.append(
                                    raw
                                )

                            writer.writerow(
                                [
                                    datetime.now().isoformat(),
                                    (
                                        "CAPTURE"
                                        if in_capture
                                        else "HOLD"
                                    ),
                                    round(
                                        now - start,
                                        6,
                                    ),
                                    round(
                                        hold_elapsed,
                                        6,
                                    ),
                                    raw,
                                    (
                                        ""
                                        if median9 is None
                                        else median9
                                    ),
                                    bool(
                                        state["Enable"]
                                    ),
                                    int(state["DAC"]),
                                    bool(
                                        state[
                                            "AppliedEnable"
                                        ]
                                    ),
                                    int(
                                        state[
                                            "AppliedDAC"
                                        ]
                                    ),
                                    bool(
                                        state[
                                            "WatchdogHealthy"
                                        ]
                                    ),
                                    bool(
                                        state[
                                            "WatchdogTripped"
                                        ]
                                    ),
                                ]
                            )
                            sf.flush()

                            if (
                                now - last_print
                                >= 0.25
                            ):
                                mtext = (
                                    "n/a"
                                    if median9 is None
                                    else f"{median9:.1f}"
                                )
                                remaining = max(
                                    0.0,
                                    hold_end - now,
                                )
                                label = (
                                    "MEASURE NOW"
                                    if in_capture
                                    else "HOLD"
                                )
                                print(
                                    f"{label:11s} | "
                                    f"t_hold="
                                    f"{hold_elapsed:5.2f}s | "
                                    f"remaining="
                                    f"{remaining:4.1f}s | "
                                    f"Nivel={raw:4d} | "
                                    f"Median9="
                                    f"{mtext:>6} | "
                                    f"AppliedDAC="
                                    f"{int(state['AppliedDAC']):5d}"
                                )
                                last_print = now

                            if not healthy(state):
                                raise RuntimeError(
                                    "watchdog became invalid "
                                    "during hold: "
                                    + state_text(
                                        state
                                    )
                                )

                            if (
                                int(
                                    state[
                                        "AppliedDAC"
                                    ]
                                )
                                != a.target_dac
                            ):
                                raise RuntimeError(
                                    "Applied DAC left the "
                                    "requested plateau: "
                                    + state_text(
                                        state
                                    )
                                )

                            if (
                                soft_stop_hits
                                >= SOFT_STOP_CONSECUTIVE
                            ):
                                soft_stop_triggered = True
                                print(
                                    "Rolling-median raw soft "
                                    "stop reached during hold."
                                )
                                break

                            await asyncio.sleep(
                                a.sample_s
                            )

                        hold_completed = (
                            not soft_stop_triggered
                        )

                    print(
                        "Stopping pump automatically..."
                    )
                    await force_zero()

                finally:
                    await force_zero()
                    print(
                        "Final PLC zero-output "
                        "verification: PASSED"
                    )

    if not capture_samples:
        print()
        print(
            "No valid final capture interval "
            "was collected."
        )
        print(
            "Do not record a calibration point "
            "from this run."
        )
        print(
            f"Samples CSV: {samples_path}"
        )
        return 2

    raw_min = min(capture_samples)
    raw_max = max(capture_samples)
    raw_median = statistics.median(
        capture_samples
    )
    raw_mean = statistics.fmean(
        capture_samples
    )

    print()
    print("FINAL PLATEAU CAPTURE")
    print("=====================")
    print(
        f"Hold completed: "
        f"{'YES' if hold_completed else 'NO'}"
    )
    print(
        f"Soft stop triggered: "
        f"{'YES' if soft_stop_triggered else 'NO'}"
    )
    print(
        f"Capture samples: "
        f"{len(capture_samples)}"
    )
    print(f"Raw min: {raw_min}")
    print(f"Raw max: {raw_max}")
    print(
        f"Raw median: {raw_median:.3f}"
    )
    print(
        f"Raw mean: {raw_mean:.3f}"
    )
    print(
        f"Raw peak-to-peak: "
        f"{raw_max - raw_min}"
    )
    print()
    print(
        "Enter the PHYSICAL HEIGHT observed "
        "while 'MEASURE NOW' was on screen."
    )

    while True:
        text = input(
            "Observed height in cm, or Q to discard this point: "
        ).strip()

        if text.upper() == "Q":
            print(
                "Calibration point discarded."
            )
            print(
                f"Samples CSV: {samples_path}"
            )
            return 0

        try:
            height_cm = float(
                text.replace(",", ".")
            )
        except ValueError:
            print("Invalid height.")
            continue

        if height_cm < 0:
            print(
                "Height cannot be negative."
            )
            continue

        break

    with point_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as pf:
        writer = csv.writer(
            pf,
            delimiter=";",
        )
        writer.writerow(
            [
                "timestamp",
                "height_cm_observed_during_plateau",
                "raw_min",
                "raw_max",
                "raw_median",
                "raw_mean",
                "raw_peak_to_peak",
                "target_dac",
                "estimated_hz",
                "hold_s",
                "capture_tail_s",
                "hold_completed",
                "soft_stop_triggered",
            ]
        )
        writer.writerow(
            [
                datetime.now().isoformat(),
                height_cm,
                raw_min,
                raw_max,
                round(
                    raw_median,
                    6,
                ),
                round(
                    raw_mean,
                    6,
                ),
                raw_max - raw_min,
                a.target_dac,
                round(
                    estimated_hz(
                        a.target_dac
                    ),
                    6,
                ),
                a.hold_s,
                a.capture_tail_s,
                hold_completed,
                soft_stop_triggered,
            ]
        )

    print()
    print(
        f"Calibration point recorded: "
        f"{height_cm:.2f} cm -> "
        f"{raw_median:.3f} raw at "
        f"DAC={a.target_dac} "
        f"(~{estimated_hz(a.target_dac):.2f} Hz estimated)"
    )
    print(
        f"Samples CSV: {samples_path}"
    )
    print(
        f"Calibration point CSV: "
        f"{point_path}"
    )
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

    return asyncio.run(
        execute(a)
    )


if __name__ == "__main__":
    raise SystemExit(main())
