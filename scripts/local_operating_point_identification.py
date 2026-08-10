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

TOKEN = "LOCAL_IDENTIFICATION_READY"

STAGE_DAC_MAX = 12300
MEDIAN_WINDOW = 9
RATE_WINDOW_S = 1.0
ZERO_VERIFY_SAMPLES = 5
ZERO_VERIFY_TIMEOUT_S = 25.0
TRIP_CONFIRMATIONS = 3

STABILITY_WINDOW_S = 5.0
STABILITY_MAX_ABS_SLOPE_RAW_PER_S = 12.0
STABILITY_MAX_MEDIAN_RANGE_RAW = 120.0
STABILITY_REQUIRED_CONFIRMATIONS = 8

PLC_IDS = {
    "Nivel": "ns=6;s=::Program:Nivel",
    "Enable": "ns=6;s=::Program:Enable",
    "DAC": "ns=6;s=::Program:DAC",
    "Heartbeat": "ns=6;s=::Program:Heartbeat",
    "SafetyReset": "ns=6;s=::Program:SafetyReset",
    "WatchdogHealthy": "ns=6;s=::Program:WatchdogHealthy",
    "WatchdogTripped": "ns=6;s=::Program:WatchdogTripped",
    "AppliedEnable": "ns=6;s=::Program:AppliedEnable",
    "AppliedDAC": "ns=6;s=::Program:AppliedDAC",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local operating-point identification V3. The plant is first "
            "filled at a reviewed startup DAC, then transferred to a lower "
            "base DAC and required to satisfy a multi-second stationarity "
            "criterion before repeated identification perturbations."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")

    parser.add_argument("--startup-dac", type=int, required=True)
    parser.add_argument("--startup-target-raw", type=float, required=True)
    parser.add_argument("--base-dac", type=int, required=True)
    parser.add_argument("--high-dac", type=int, required=True)

    parser.add_argument("--operating-min-raw", type=float, required=True)
    parser.add_argument("--operating-max-raw", type=float, required=True)

    parser.add_argument("--maximum-level-raw", type=float, required=True)
    parser.add_argument(
        "--maximum-level-rate-raw-per-s",
        type=float,
        required=True,
    )

    parser.add_argument("--startup-timeout-s", type=float, required=True)
    parser.add_argument("--settle-timeout-s", type=float, required=True)
    parser.add_argument("--baseline-s", type=float, required=True)
    parser.add_argument("--high-hold-s", type=float, required=True)
    parser.add_argument("--base-recovery-s", type=float, required=True)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--sample-s", type=float, default=0.1)
    parser.add_argument(
        "--transition-timeout-s",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--maximum-experiment-duration-s",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/raw"),
    )

    return parser


def validate(args: argparse.Namespace) -> None:
    if not (
        1
        <= args.base_dac
        < args.high_dac
        <= STAGE_DAC_MAX
    ):
        raise ValueError(
            f"require 1 <= base DAC < high DAC <= {STAGE_DAC_MAX}"
        )

    if not (
        args.base_dac
        <= args.startup_dac
        <= STAGE_DAC_MAX
    ):
        raise ValueError(
            f"startup DAC must be between base DAC and {STAGE_DAC_MAX}"
        )

    if args.startup_target_raw <= 0:
        raise ValueError("startup target raw must be positive")

    if args.operating_min_raw >= args.operating_max_raw:
        raise ValueError(
            "operating minimum must be below operating maximum"
        )

    if args.operating_max_raw >= args.maximum_level_raw:
        raise ValueError(
            "operating maximum must be below maximum raw trip"
        )

    if not (
        args.operating_min_raw
        <= args.startup_target_raw
        <= args.operating_max_raw
    ):
        raise ValueError(
            "startup target raw must lie inside the operating band"
        )

    if args.maximum_level_rate_raw_per_s <= 0:
        raise ValueError("maximum level rate must be positive")

    timings = (
        args.startup_timeout_s,
        args.settle_timeout_s,
        args.baseline_s,
        args.high_hold_s,
        args.base_recovery_s,
        args.sample_s,
        args.transition_timeout_s,
        args.maximum_experiment_duration_s,
    )

    if any(value <= 0 for value in timings):
        raise ValueError("all timing values must be positive")

    if args.cycles != 2:
        raise ValueError(
            "this validation-stage script requires exactly 2 cycles"
        )

    nominal_after_settle = (
        args.baseline_s
        + args.cycles
        * (
            args.high_hold_s
            + args.base_recovery_s
        )
    )

    if (
        args.maximum_experiment_duration_s
        <= nominal_after_settle
    ):
        raise ValueError(
            "maximum experiment duration must exceed the post-settle sequence"
        )


def print_plan(args: argparse.Namespace) -> None:
    print("LOCAL OPERATING-POINT IDENTIFICATION PLAN V3")
    print("============================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"Stage DAC ceiling: {STAGE_DAC_MAX}")
    print(f"Startup DAC: {args.startup_dac}")
    print(f"Startup filtered-level target: {args.startup_target_raw:.1f} raw")
    print(f"Base DAC: {args.base_dac}")
    print(f"High DAC: {args.high_dac}")
    print(
        "Perturbation amplitude: "
        f"+{args.high_dac - args.base_dac} DAC"
    )
    print(
        "Operating raw band: "
        f"{args.operating_min_raw:.1f} .. "
        f"{args.operating_max_raw:.1f}"
    )
    print(
        "Stationarity requirement: "
        f"{STABILITY_WINDOW_S:.1f} s window, "
        f"|slope| <= {STABILITY_MAX_ABS_SLOPE_RAW_PER_S:.1f} raw/s, "
        f"median range <= {STABILITY_MAX_MEDIAN_RANGE_RAW:.1f} raw"
    )
    print(
        f"Maximum rolling-median raw level: "
        f"{args.maximum_level_raw:.1f}"
    )
    print(
        "Maximum positive rolling-median rate: "
        f"{args.maximum_level_rate_raw_per_s:.1f} raw/s"
    )
    print(f"Startup timeout: {args.startup_timeout_s:.1f} s")
    print(f"Base-settle timeout: {args.settle_timeout_s:.1f} s")
    print(f"Baseline at base DAC: {args.baseline_s:.1f} s")
    print(f"High hold per cycle: {args.high_hold_s:.1f} s")
    print(
        f"Base recovery per cycle: "
        f"{args.base_recovery_s:.1f} s"
    )
    print("Cycles: 2")
    print(f"Sampling period requested: {args.sample_s:.3f} s")
    print(
        "Applied-DAC transition timeout: "
        f"{args.transition_timeout_s:.1f} s"
    )
    print(
        "Maximum total experiment duration: "
        f"{args.maximum_experiment_duration_s:.1f} s"
    )
    print()
    print("Sequence:")
    print("  STARTUP_FILL @ startup DAC")
    print("  SETTLE_BASE  @ base DAC")
    print("  BASELINE")
    print("  HIGH_1")
    print("  BASE_1")
    print("  HIGH_2")
    print("  BASE_2")
    print()
    print(
        "Identification perturbations are not allowed until the "
        "multi-second stationarity criterion has passed."
    )
    print()
    print(f"Run confirmation token: {TOKEN}")


def zero_state(state: dict[str, object]) -> bool:
    return (
        state["Enable"] is False
        and int(state["DAC"]) == 0
        and state["AppliedEnable"] is False
        and int(state["AppliedDAC"]) == 0
    )


def healthy(state: dict[str, object]) -> bool:
    return (
        state["SafetyReset"] is False
        and state["WatchdogHealthy"] is True
        and state["WatchdogTripped"] is False
    )


def state_text(state: dict[str, object]) -> str:
    return (
        f"Enable={bool(state['Enable'])} "
        f"DAC={int(state['DAC'])} "
        f"AppliedEnable={bool(state['AppliedEnable'])} "
        f"AppliedDAC={int(state['AppliedDAC'])} "
        f"Healthy={bool(state['WatchdogHealthy'])} "
        f"Tripped={bool(state['WatchdogTripped'])}"
    )


class SignalGuard:
    def __init__(
        self,
        *,
        maximum_level_raw: float,
        maximum_rate_raw_per_s: float,
    ) -> None:
        self.maximum_level_raw = maximum_level_raw
        self.maximum_rate_raw_per_s = maximum_rate_raw_per_s
        self.raw_window: deque[float] = deque(
            maxlen=MEDIAN_WINDOW
        )
        self.rate_history: deque[tuple[float, float]] = deque()
        self.level_trip_count = 0
        self.rate_trip_count = 0

    def update(
        self,
        *,
        timestamp_s: float,
        raw: float,
    ) -> tuple[float | None, float | None]:
        self.raw_window.append(raw)

        median_value = None
        rate_value = None

        if len(self.raw_window) == MEDIAN_WINDOW:
            median_value = float(
                statistics.median(self.raw_window)
            )
            self.rate_history.append(
                (timestamp_s, median_value)
            )

            while (
                len(self.rate_history) >= 2
                and timestamp_s - self.rate_history[1][0]
                >= RATE_WINDOW_S
            ):
                self.rate_history.popleft()

            if len(self.rate_history) >= 2:
                first_t, first_y = self.rate_history[0]
                span = timestamp_s - first_t

                if span >= RATE_WINDOW_S * 0.75:
                    rate_value = (
                        median_value - first_y
                    ) / span

            if median_value >= self.maximum_level_raw:
                self.level_trip_count += 1
            else:
                self.level_trip_count = 0

            if (
                rate_value is not None
                and rate_value
                > self.maximum_rate_raw_per_s
            ):
                self.rate_trip_count += 1
            else:
                self.rate_trip_count = 0

            if self.level_trip_count >= TRIP_CONFIRMATIONS:
                raise RuntimeError(
                    "rolling-median raw-level trip reached: "
                    f"{median_value:.3f} >= "
                    f"{self.maximum_level_raw:.3f}"
                )

            if self.rate_trip_count >= TRIP_CONFIRMATIONS:
                raise RuntimeError(
                    "positive rolling-median rate trip reached: "
                    f"{rate_value:.3f} > "
                    f"{self.maximum_rate_raw_per_s:.3f} raw/s"
                )

        return median_value, rate_value


class StabilityWindow:
    def __init__(self) -> None:
        self.values: deque[tuple[float, float]] = deque()

    def update(
        self,
        timestamp_s: float,
        median_value: float | None,
    ) -> tuple[bool, float | None, float | None]:
        if median_value is None:
            return False, None, None

        self.values.append(
            (timestamp_s, median_value)
        )

        while (
            len(self.values) >= 2
            and timestamp_s - self.values[0][0]
            > STABILITY_WINDOW_S
        ):
            self.values.popleft()

        if len(self.values) < 2:
            return False, None, None

        span = (
            self.values[-1][0]
            - self.values[0][0]
        )

        if span < STABILITY_WINDOW_S * 0.9:
            return False, None, None

        xs = [item[0] for item in self.values]
        ys = [item[1] for item in self.values]

        x_mean = statistics.fmean(xs)
        y_mean = statistics.fmean(ys)

        denominator = sum(
            (x - x_mean) ** 2
            for x in xs
        )

        if denominator <= 0:
            return False, None, None

        slope = (
            sum(
                (x - x_mean) * (y - y_mean)
                for x, y in zip(xs, ys)
            )
            / denominator
        )

        value_range = max(ys) - min(ys)

        stable = (
            abs(slope)
            <= STABILITY_MAX_ABS_SLOPE_RAW_PER_S
            and value_range
            <= STABILITY_MAX_MEDIAN_RANGE_RAW
        )

        return stable, slope, value_range


async def execute(args: argparse.Namespace) -> Path:
    from asyncua import Client, ua

    confirmation = input(
        "Type LOCAL_IDENTIFICATION_READY only if: physical stop "
        "accessible, FORTE stopped, gateway running, tank visually "
        "safe, and the 12300-DAC stage ceiling is accepted: "
    ).strip()

    if confirmation != TOKEN:
        raise RuntimeError(
            "local identification was not confirmed"
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = (
        args.output_root
        / f"local-identification-v3-{stamp}"
    )
    folder.mkdir(parents=True, exist_ok=False)

    csv_path = folder / "local-identification.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "phase_elapsed_s",
        "level_raw",
        "rolling_median_level",
        "rolling_median_rate_raw_per_s",
        "stability_slope_raw_per_s",
        "stability_range_raw",
        "requested_phase_dac",
        "enable",
        "dac",
        "applied_enable",
        "applied_dac",
        "heartbeat",
        "watchdog_healthy",
        "watchdog_tripped",
        "safety_reset",
    ]

    start = time.monotonic()

    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as plc:
        async with Client(
            GATEWAY_ENDPOINT,
            timeout=5.0,
        ) as gateway:
            namespace_index = await gateway.get_namespace_index(
                GATEWAY_URI
            )

            enable_node = gateway.get_node(
                ua.NodeId("Enable", namespace_index)
            )
            dac_node = gateway.get_node(
                ua.NodeId("DAC", namespace_index)
            )

            plc_nodes = {
                name: plc.get_node(node_id)
                for name, node_id in PLC_IDS.items()
            }

            async def read_state() -> dict[str, object]:
                return {
                    name: await node.read_value()
                    for name, node in plc_nodes.items()
                }

            async def write_only(
                node,
                value,
                variant_type,
            ) -> None:
                await node.write_attribute(
                    ua.AttributeIds.Value,
                    ua.DataValue(
                        ua.Variant(
                            value,
                            variant_type,
                        )
                    ),
                )

            async def force_zero() -> None:
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
                    "watchdog is not healthy before experiment: "
                    + state_text(initial)
                )

            if not zero_state(initial):
                raise RuntimeError(
                    "experiment must start at complete zero output: "
                    + state_text(initial)
                )

            guard = SignalGuard(
                maximum_level_raw=args.maximum_level_raw,
                maximum_rate_raw_per_s=(
                    args.maximum_level_rate_raw_per_s
                ),
            )

            stability = StabilityWindow()

            current_phase = "START"
            phase_start = time.monotonic()
            requested_phase_dac = 0
            last_print = 0.0
            current_stability_slope = None
            current_stability_range = None

            with csv_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=fields,
                    delimiter=";",
                )
                writer.writeheader()

                async def sample():
                    nonlocal last_print
                    nonlocal current_stability_slope
                    nonlocal current_stability_range

                    state = await read_state()
                    now = time.monotonic()
                    elapsed = now - start

                    if (
                        elapsed
                        >= args.maximum_experiment_duration_s
                    ):
                        raise RuntimeError(
                            "maximum experiment duration reached"
                        )

                    if not healthy(state):
                        raise RuntimeError(
                            "watchdog became invalid: "
                            + state_text(state)
                        )

                    raw = float(state["Nivel"])

                    median_value, rate_value = guard.update(
                        timestamp_s=now,
                        raw=raw,
                    )

                    stability_ok = False

                    if current_phase == "SETTLE_BASE":
                        (
                            stability_ok,
                            current_stability_slope,
                            current_stability_range,
                        ) = stability.update(
                            now,
                            median_value,
                        )
                    else:
                        current_stability_slope = None
                        current_stability_range = None

                    writer.writerow(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "elapsed_s": round(elapsed, 6),
                            "phase": current_phase,
                            "phase_elapsed_s": round(
                                now - phase_start,
                                6,
                            ),
                            "level_raw": raw,
                            "rolling_median_level": (
                                ""
                                if median_value is None
                                else round(median_value, 6)
                            ),
                            "rolling_median_rate_raw_per_s": (
                                ""
                                if rate_value is None
                                else round(rate_value, 6)
                            ),
                            "stability_slope_raw_per_s": (
                                ""
                                if current_stability_slope is None
                                else round(
                                    current_stability_slope,
                                    6,
                                )
                            ),
                            "stability_range_raw": (
                                ""
                                if current_stability_range is None
                                else round(
                                    current_stability_range,
                                    6,
                                )
                            ),
                            "requested_phase_dac": requested_phase_dac,
                            "enable": bool(state["Enable"]),
                            "dac": int(state["DAC"]),
                            "applied_enable": bool(
                                state["AppliedEnable"]
                            ),
                            "applied_dac": int(
                                state["AppliedDAC"]
                            ),
                            "heartbeat": int(state["Heartbeat"]),
                            "watchdog_healthy": bool(
                                state["WatchdogHealthy"]
                            ),
                            "watchdog_tripped": bool(
                                state["WatchdogTripped"]
                            ),
                            "safety_reset": bool(
                                state["SafetyReset"]
                            ),
                        }
                    )
                    stream.flush()

                    if now - last_print >= 0.5:
                        med_text = (
                            "n/a"
                            if median_value is None
                            else f"{median_value:.1f}"
                        )
                        rate_text = (
                            "n/a"
                            if rate_value is None
                            else f"{rate_value:.1f}"
                        )
                        slope_text = (
                            "n/a"
                            if current_stability_slope is None
                            else f"{current_stability_slope:.1f}"
                        )
                        range_text = (
                            "n/a"
                            if current_stability_range is None
                            else f"{current_stability_range:.0f}"
                        )

                        print(
                            f"{current_phase:12s} | "
                            f"Nivel={int(raw):4d} | "
                            f"Median9={med_text:>6s} | "
                            f"Rate={rate_text:>7s} | "
                            f"StableSlope={slope_text:>6s} | "
                            f"StableRange={range_text:>4s} | "
                            f"AppliedDAC={int(state['AppliedDAC']):5d}"
                        )
                        last_print = now

                    return (
                        state,
                        median_value,
                        rate_value,
                        stability_ok,
                    )

                async def change_target(
                    *,
                    phase_name: str,
                    target_dac: int,
                ) -> None:
                    nonlocal current_phase
                    nonlocal phase_start
                    nonlocal requested_phase_dac
                    nonlocal stability

                    current_phase = phase_name
                    phase_start = time.monotonic()
                    requested_phase_dac = target_dac

                    if phase_name == "SETTLE_BASE":
                        stability = StabilityWindow()

                    await write_only(
                        enable_node,
                        True,
                        ua.VariantType.Boolean,
                    )
                    await write_only(
                        dac_node,
                        target_dac,
                        ua.VariantType.Int16,
                    )

                    deadline = (
                        time.monotonic()
                        + args.transition_timeout_s
                    )

                    while time.monotonic() < deadline:
                        state, _, _, _ = await sample()

                        if (
                            state["AppliedEnable"] is True
                            and int(state["AppliedDAC"])
                            == target_dac
                        ):
                            return

                        await asyncio.sleep(args.sample_s)

                    raise RuntimeError(
                        f"{phase_name}: applied DAC did not reach "
                        f"{target_dac}"
                    )

                async def hold_for(
                    duration_s: float,
                ) -> None:
                    deadline = time.monotonic() + duration_s

                    while time.monotonic() < deadline:
                        state, _, _, _ = await sample()

                        if (
                            state["AppliedEnable"] is not True
                            or int(state["AppliedDAC"])
                            != requested_phase_dac
                        ):
                            raise RuntimeError(
                                "applied output left requested plateau: "
                                + state_text(state)
                            )

                        await asyncio.sleep(args.sample_s)

                try:
                    print(
                        f"Startup fill: ramping to DAC={args.startup_dac}..."
                    )

                    await change_target(
                        phase_name="STARTUP_FILL",
                        target_dac=args.startup_dac,
                    )

                    startup_deadline = (
                        time.monotonic()
                        + args.startup_timeout_s
                    )

                    print(
                        "Waiting until filtered level reaches "
                        f"{args.startup_target_raw:.1f} raw..."
                    )

                    while time.monotonic() < startup_deadline:
                        _, median_value, _, _ = await sample()

                        if (
                            median_value is not None
                            and median_value
                            >= args.startup_target_raw
                        ):
                            print(
                                "Startup filtered-level target: PASSED"
                            )
                            break

                        await asyncio.sleep(args.sample_s)
                    else:
                        raise RuntimeError(
                            "startup filtered-level target was not "
                            "reached before timeout"
                        )

                    print(
                        f"Transferring to base DAC={args.base_dac}..."
                    )

                    await change_target(
                        phase_name="SETTLE_BASE",
                        target_dac=args.base_dac,
                    )

                    settle_deadline = (
                        time.monotonic()
                        + args.settle_timeout_s
                    )
                    stable_confirmations = 0

                    print(
                        "Waiting for a genuinely stationary base point..."
                    )

                    while time.monotonic() < settle_deadline:
                        (
                            _,
                            median_value,
                            _,
                            stability_ok,
                        ) = await sample()

                        in_band = (
                            median_value is not None
                            and args.operating_min_raw
                            <= median_value
                            <= args.operating_max_raw
                        )

                        valid = (
                            in_band
                            and stability_ok
                        )

                        stable_confirmations = (
                            stable_confirmations + 1
                            if valid
                            else 0
                        )

                        if (
                            stable_confirmations
                            >= STABILITY_REQUIRED_CONFIRMATIONS
                        ):
                            print(
                                "Stationary base operating point: PASSED"
                            )
                            break

                        await asyncio.sleep(args.sample_s)
                    else:
                        raise RuntimeError(
                            "base operating point did not satisfy the "
                            "stationarity criterion before timeout"
                        )

                    await change_target(
                        phase_name="BASELINE",
                        target_dac=args.base_dac,
                    )
                    await hold_for(args.baseline_s)

                    for cycle in range(1, args.cycles + 1):
                        await change_target(
                            phase_name=f"HIGH_{cycle}",
                            target_dac=args.high_dac,
                        )
                        await hold_for(args.high_hold_s)

                        await change_target(
                            phase_name=f"BASE_{cycle}",
                            target_dac=args.base_dac,
                        )
                        await hold_for(args.base_recovery_s)

                    print(
                        "Local identification sequence: PASSED"
                    )
                    print(f"CSV: {csv_path}")

                finally:
                    await force_zero()
                    print(
                        "Final PLC zero-output verification: PASSED"
                    )

    return csv_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate(args)
    except ValueError as error:
        parser.error(str(error))

    if args.plan:
        print_plan(args)
        return 0

    asyncio.run(execute(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
