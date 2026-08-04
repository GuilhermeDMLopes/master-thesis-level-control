from __future__ import annotations

import argparse
import asyncio
import csv
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Sequence


DEFAULT_PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
DEFAULT_GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
DEFAULT_GATEWAY_URI = "urn:br-4diac-gateway"
DEFAULT_BASELINE_S = 8.0
DEFAULT_RECOVERY_S = 10.0
DEFAULT_SAMPLE_S = 0.10
DEFAULT_LEVEL_RATE_WINDOW_S = 1.0
DAC_MIN = 0
DAC_MAX = 32000
CONFIRMATION_TOKEN = "IDENTIFICATION_READY"
FINAL_SAFE_SAMPLES = 5
FINAL_SAFE_TIMEOUT_S = 5.0
FINAL_SAFE_SAMPLE_S = 0.25

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


@dataclass(frozen=True)
class ExcitationStep:
    dac: int
    hold_s: float

    def validate(self) -> None:
        if not 0 < self.dac <= DAC_MAX:
            raise ValueError(
                f"Step DAC must be between 1 and {DAC_MAX}."
            )
        if self.hold_s <= 0.0:
            raise ValueError(
                "Step hold duration must be greater than zero."
            )


@dataclass(frozen=True)
class IdentificationConfig:
    plc_endpoint: str
    gateway_endpoint: str
    gateway_uri: str
    steps: tuple[ExcitationStep, ...]
    initial_level_min_raw: int | None
    initial_level_max_raw: int | None
    maximum_level_raw: int | None
    maximum_level_rate_raw_per_s: float | None
    maximum_experiment_duration_s: float | None
    level_rate_window_s: float
    baseline_s: float
    recovery_s: float
    sample_s: float
    output_root: Path

    @property
    def nominal_recording_duration_s(self) -> float:
        return (
            self.baseline_s
            + sum(step.hold_s for step in self.steps)
            + self.recovery_s
        )

    def validate(self, *, execute: bool) -> None:
        if not self.plc_endpoint.strip():
            raise ValueError("PLC endpoint must not be empty.")
        if not self.gateway_endpoint.strip():
            raise ValueError("Gateway endpoint must not be empty.")
        if not self.gateway_uri.strip():
            raise ValueError("Gateway namespace URI must not be empty.")

        for step in self.steps:
            step.validate()

        if execute and not self.steps:
            raise ValueError(
                "At least one --dac-step is required with --execute."
            )
        if execute and self.maximum_level_raw is None:
            raise ValueError(
                "--maximum-level-raw is required with --execute."
            )
        if execute and self.initial_level_min_raw is None:
            raise ValueError(
                "--initial-level-min-raw is required with --execute."
            )
        if execute and self.initial_level_max_raw is None:
            raise ValueError(
                "--initial-level-max-raw is required with --execute."
            )
        if execute and self.maximum_level_rate_raw_per_s is None:
            raise ValueError(
                "--maximum-level-rate-raw-per-s is required "
                "with --execute."
            )
        if execute and self.maximum_experiment_duration_s is None:
            raise ValueError(
                "--maximum-experiment-duration-s is required "
                "with --execute."
            )

        optional_nonnegative = (
            ("Initial minimum raw level", self.initial_level_min_raw),
            ("Initial maximum raw level", self.initial_level_max_raw),
            ("Maximum raw level", self.maximum_level_raw),
        )
        for name, value in optional_nonnegative:
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative.")

        if (
            self.initial_level_min_raw is not None
            and self.initial_level_max_raw is not None
            and self.initial_level_min_raw
            >= self.initial_level_max_raw
        ):
            raise ValueError(
                "Initial raw-level minimum must be lower than "
                "the initial raw-level maximum."
            )

        if (
            self.initial_level_max_raw is not None
            and self.maximum_level_raw is not None
            and self.initial_level_max_raw
            >= self.maximum_level_raw
        ):
            raise ValueError(
                "Initial raw-level maximum must be lower than "
                "the maximum raw-level trip threshold."
            )

        if (
            self.maximum_level_rate_raw_per_s is not None
            and self.maximum_level_rate_raw_per_s <= 0.0
        ):
            raise ValueError(
                "Maximum level rate must be greater than zero."
            )
        if (
            self.maximum_experiment_duration_s is not None
            and self.maximum_experiment_duration_s <= 0.0
        ):
            raise ValueError(
                "Maximum experiment duration must be greater than zero."
            )
        if (
            self.maximum_experiment_duration_s is not None
            and self.maximum_experiment_duration_s
            <= self.nominal_recording_duration_s
        ):
            raise ValueError(
                "Maximum experiment duration must exceed the nominal "
                "baseline, hold, and recovery duration."
            )
        if self.level_rate_window_s <= 0.0:
            raise ValueError(
                "Level-rate window must be greater than zero."
            )
        if self.baseline_s < 0.0:
            raise ValueError(
                "Baseline duration must not be negative."
            )
        if self.recovery_s < 0.0:
            raise ValueError(
                "Recovery duration must not be negative."
            )
        if self.sample_s <= 0.0:
            raise ValueError(
                "Sampling period must be greater than zero."
            )
        if self.level_rate_window_s < self.sample_s * 2.0:
            raise ValueError(
                "Level-rate window must span at least two "
                "sampling periods."
            )


class PositiveLevelRateGuard:
    def __init__(
        self,
        *,
        maximum_rate_raw_per_s: float,
        window_s: float,
    ) -> None:
        if maximum_rate_raw_per_s <= 0.0:
            raise ValueError(
                "Maximum level rate must be greater than zero."
            )
        if window_s <= 0.0:
            raise ValueError(
                "Level-rate window must be greater than zero."
            )

        self.maximum_rate_raw_per_s = maximum_rate_raw_per_s
        self.window_s = window_s
        self._samples: Deque[tuple[float, int]] = deque()

    def observe(
        self,
        *,
        timestamp_s: float,
        level_raw: int,
    ) -> float | None:
        self._samples.append((timestamp_s, level_raw))

        while (
            len(self._samples) >= 3
            and timestamp_s - self._samples[1][0]
            >= self.window_s
        ):
            self._samples.popleft()

        if len(self._samples) < 2:
            return None

        first_time, first_level = self._samples[0]
        span_s = timestamp_s - first_time

        if span_s < self.window_s * 0.5:
            return None

        rate = (level_raw - first_level) / span_s

        if rate > self.maximum_rate_raw_per_s:
            raise RuntimeError(
                "Maximum positive raw-level rate exceeded: "
                f"{rate:.3f} > "
                f"{self.maximum_rate_raw_per_s:.3f} raw-count/s."
            )

        return rate


def parse_dac_step(value: str) -> ExcitationStep:
    parts = value.split(":", maxsplit=1)

    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            "DAC step must use DAC:HOLD_S format."
        )

    try:
        dac = int(parts[0])
        hold_s = float(parts[1])
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "DAC step must contain an integer DAC and "
            "a numeric hold duration."
        ) from error

    step = ExcitationStep(dac=dac, hold_s=hold_s)

    try:
        step.validate()
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error

    return step


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect or execute a multi-step real-plant "
            "open-loop identification sequence. Network access "
            "and actuator writes occur only with --execute. "
            "No excitation or physical-limit values are supplied "
            "by default."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help="print the resolved plan without network access",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "run after validation and interactive confirmation"
        ),
    )

    parser.add_argument(
        "--plc-endpoint",
        default=DEFAULT_PLC_ENDPOINT,
    )
    parser.add_argument(
        "--gateway-endpoint",
        default=DEFAULT_GATEWAY_ENDPOINT,
    )
    parser.add_argument(
        "--gateway-uri",
        default=DEFAULT_GATEWAY_URI,
    )
    parser.add_argument(
        "--dac-step",
        type=parse_dac_step,
        action="append",
        default=[],
        metavar="DAC:HOLD_S",
        help=(
            "append one reviewed positive-DAC plateau; repeat "
            "to build the sequence"
        ),
    )
    parser.add_argument(
        "--initial-level-min-raw",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--initial-level-max-raw",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--maximum-level-raw",
        type=int,
        default=None,
        help=(
            "upper raw-level abort threshold; mandatory "
            "with --execute"
        ),
    )
    parser.add_argument(
        "--maximum-level-rate-raw-per-s",
        type=float,
        default=None,
        help=(
            "maximum positive raw-level rate over the configured "
            "window; mandatory with --execute"
        ),
    )
    parser.add_argument(
        "--maximum-experiment-duration-s",
        type=float,
        default=None,
        help=(
            "hard elapsed-time abort; mandatory with --execute"
        ),
    )
    parser.add_argument(
        "--level-rate-window-s",
        type=float,
        default=DEFAULT_LEVEL_RATE_WINDOW_S,
    )
    parser.add_argument(
        "--baseline-s",
        type=float,
        default=DEFAULT_BASELINE_S,
    )
    parser.add_argument(
        "--recovery-s",
        type=float,
        default=DEFAULT_RECOVERY_S,
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=DEFAULT_SAMPLE_S,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/raw"),
    )

    return parser


def config_from_args(
    args: argparse.Namespace,
) -> IdentificationConfig:
    return IdentificationConfig(
        plc_endpoint=args.plc_endpoint,
        gateway_endpoint=args.gateway_endpoint,
        gateway_uri=args.gateway_uri,
        steps=tuple(args.dac_step),
        initial_level_min_raw=args.initial_level_min_raw,
        initial_level_max_raw=args.initial_level_max_raw,
        maximum_level_raw=args.maximum_level_raw,
        maximum_level_rate_raw_per_s=(
            args.maximum_level_rate_raw_per_s
        ),
        maximum_experiment_duration_s=(
            args.maximum_experiment_duration_s
        ),
        level_rate_window_s=args.level_rate_window_s,
        baseline_s=args.baseline_s,
        recovery_s=args.recovery_s,
        sample_s=args.sample_s,
        output_root=args.output_root,
    )


def optional_value(
    value: object | None,
    *,
    required_text: str,
) -> str:
    if value is None:
        return f"NOT SET ({required_text})"

    return str(value)


def print_plan(config: IdentificationConfig) -> None:
    print("MULTI-STEP OPEN-LOOP IDENTIFICATION PLAN")
    print("========================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"PLC endpoint: {config.plc_endpoint}")
    print(f"Gateway endpoint: {config.gateway_endpoint}")
    print(f"Gateway URI: {config.gateway_uri}")

    if config.steps:
        print("DAC sequence:")
        for index, step in enumerate(config.steps, start=1):
            print(
                f"  step {index}: DAC={step.dac}, "
                f"hold={step.hold_s:.3f} s"
            )
    else:
        print(
            "DAC sequence: NOT SET "
            "(required for --execute)"
        )

    print(
        "Initial raw-level minimum: "
        + optional_value(
            config.initial_level_min_raw,
            required_text="required for --execute",
        )
    )
    print(
        "Initial raw-level maximum: "
        + optional_value(
            config.initial_level_max_raw,
            required_text="required for --execute",
        )
    )
    print(
        "Maximum raw-level trip: "
        + optional_value(
            config.maximum_level_raw,
            required_text="required for --execute",
        )
    )
    print(
        "Maximum positive raw-level rate: "
        + optional_value(
            config.maximum_level_rate_raw_per_s,
            required_text="required for --execute",
        )
    )
    print(
        "Maximum experiment duration: "
        + optional_value(
            config.maximum_experiment_duration_s,
            required_text="required for --execute",
        )
    )
    print(
        f"Level-rate window: {config.level_rate_window_s:.3f} s"
    )
    print(f"Baseline duration: {config.baseline_s:.3f} s")
    print(f"Recovery duration: {config.recovery_s:.3f} s")
    print(
        "Nominal recording duration: "
        f"{config.nominal_recording_duration_s:.3f} s"
    )
    print(f"Sampling period: {config.sample_s:.3f} s")
    print(f"Output root: {config.output_root}")
    print()
    print(
        "Execution requires --execute, all required limits, "
        "at least one --dac-step, and the token:"
    )
    print(CONFIRMATION_TOKEN)


def watchdog_ok(state: dict[str, object]) -> bool:
    return (
        state["SafetyReset"] is False
        and state["WatchdogHealthy"] is True
        and state["WatchdogTripped"] is False
    )


def initial_level_ok(
    level_raw: int,
    config: IdentificationConfig,
) -> bool:
    assert config.initial_level_min_raw is not None
    assert config.initial_level_max_raw is not None

    return (
        config.initial_level_min_raw
        <= level_raw
        <= config.initial_level_max_raw
    )


async def run_experiment(
    config: IdentificationConfig,
) -> Path:
    from asyncua import Client, ua

    confirmation = input(
        "Type IDENTIFICATION_READY only after the physical "
        "stop, level limits, rate limit, duration limit, and "
        "DAC sequence have been reviewed for the real plant: "
    ).strip()

    if confirmation != CONFIRMATION_TOKEN:
        raise RuntimeError("Experiment was not confirmed.")

    assert config.steps
    assert config.initial_level_min_raw is not None
    assert config.initial_level_max_raw is not None
    assert config.maximum_level_raw is not None
    assert config.maximum_level_rate_raw_per_s is not None
    assert config.maximum_experiment_duration_s is not None

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = (
        config.output_root
        / f"open-loop-identification-{run_id}"
    )
    run_root.mkdir(parents=True, exist_ok=False)
    csv_path = run_root / "open-loop-identification.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "step_index",
        "step_dac",
        "step_hold_s",
        "level_raw",
        "level_rate_raw_per_s",
        "initial_level_min_raw",
        "initial_level_max_raw",
        "maximum_level_raw",
        "maximum_level_rate_raw_per_s",
        "maximum_experiment_duration_s",
        "heartbeat",
        "watchdog_healthy",
        "watchdog_tripped",
        "safety_reset",
        "enable_plc",
        "dac_plc",
        "applied_enable",
        "applied_dac",
        "gateway_enable_request",
        "gateway_dac_request",
    ]

    start = time.monotonic()
    last_print = 0.0
    current_step_index = 0
    current_step: ExcitationStep | None = None
    rate_guard = PositiveLevelRateGuard(
        maximum_rate_raw_per_s=(
            config.maximum_level_rate_raw_per_s
        ),
        window_s=config.level_rate_window_s,
    )

    async def write_only(node, value, variant_type) -> None:
        await node.write_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(value, variant_type)
            ),
        )

    async def read_plc(client) -> dict[str, object]:
        return {
            name: await client.get_node(node_id).read_value()
            for name, node_id in PLC_IDS.items()
        }

    async with Client(
        config.plc_endpoint,
        timeout=5.0,
    ) as plc:
        async with Client(
            config.gateway_endpoint,
            timeout=5.0,
        ) as gateway:
            namespace_index = await gateway.get_namespace_index(
                config.gateway_uri
            )
            enable_node = gateway.get_node(
                ua.NodeId("Enable", namespace_index)
            )
            dac_node = gateway.get_node(
                ua.NodeId("DAC", namespace_index)
            )

            async def sample(
                phase: str,
                writer: csv.DictWriter,
            ) -> dict[str, object]:
                nonlocal last_print

                now = time.monotonic()
                elapsed_s = now - start

                if (
                    elapsed_s
                    >= config.maximum_experiment_duration_s
                ):
                    raise RuntimeError(
                        "Maximum experiment duration reached: "
                        f"{elapsed_s:.3f} >= "
                        f"{config.maximum_experiment_duration_s:.3f} s."
                    )

                state = await read_plc(plc)
                gateway_enable = await enable_node.read_value()
                gateway_dac = await dac_node.read_value()
                level_raw = int(state["Nivel"])
                level_rate = rate_guard.observe(
                    timestamp_s=now,
                    level_raw=level_raw,
                )

                writer.writerow(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "elapsed_s": round(elapsed_s, 6),
                        "phase": phase,
                        "step_index": current_step_index,
                        "step_dac": (
                            0
                            if current_step is None
                            else current_step.dac
                        ),
                        "step_hold_s": (
                            0.0
                            if current_step is None
                            else current_step.hold_s
                        ),
                        "level_raw": level_raw,
                        "level_rate_raw_per_s": (
                            ""
                            if level_rate is None
                            else round(level_rate, 6)
                        ),
                        "initial_level_min_raw": (
                            config.initial_level_min_raw
                        ),
                        "initial_level_max_raw": (
                            config.initial_level_max_raw
                        ),
                        "maximum_level_raw": (
                            config.maximum_level_raw
                        ),
                        "maximum_level_rate_raw_per_s": (
                            config.maximum_level_rate_raw_per_s
                        ),
                        "maximum_experiment_duration_s": (
                            config.maximum_experiment_duration_s
                        ),
                        "heartbeat": int(state["Heartbeat"]),
                        "watchdog_healthy": bool(
                            state["WatchdogHealthy"]
                        ),
                        "watchdog_tripped": bool(
                            state["WatchdogTripped"]
                        ),
                        "safety_reset": bool(state["SafetyReset"]),
                        "enable_plc": bool(state["Enable"]),
                        "dac_plc": int(state["DAC"]),
                        "applied_enable": bool(
                            state["AppliedEnable"]
                        ),
                        "applied_dac": int(state["AppliedDAC"]),
                        "gateway_enable_request": bool(
                            gateway_enable
                        ),
                        "gateway_dac_request": int(gateway_dac),
                    }
                )
                writer.flush()

                if level_raw >= config.maximum_level_raw:
                    raise RuntimeError(
                        "Maximum raw-level threshold reached: "
                        f"{level_raw} >= "
                        f"{config.maximum_level_raw}."
                    )

                if now - last_print >= 0.5:
                    rate_text = (
                        "n/a"
                        if level_rate is None
                        else f"{level_rate:.2f}"
                    )
                    print(
                        f"{phase:16s} | "
                        f"t={elapsed_s:7.2f}s | "
                        f"Nivel={level_raw:5d} | "
                        f"dNivel/dt={rate_text:>7s} | "
                        f"Healthy={state['WatchdogHealthy']} | "
                        f"Tripped={state['WatchdogTripped']} | "
                        f"AppliedDAC={int(state['AppliedDAC']):5d}"
                    )
                    last_print = now

                return state

            async def record_for(
                phase: str,
                duration_s: float,
                writer: csv.DictWriter,
            ) -> None:
                deadline = time.monotonic() + duration_s

                while time.monotonic() < deadline:
                    state = await sample(phase, writer)

                    if not watchdog_ok(state):
                        raise RuntimeError(
                            f"Watchdog was invalid during {phase}."
                        )

                    await asyncio.sleep(config.sample_s)

            async def force_and_verify_safe_state() -> None:
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
                deadline = time.monotonic() + FINAL_SAFE_TIMEOUT_S

                while time.monotonic() < deadline:
                    state = await read_plc(plc)
                    safe = (
                        state["AppliedEnable"] is False
                        and int(state["AppliedDAC"]) == 0
                    )
                    stable = stable + 1 if safe else 0

                    if stable >= FINAL_SAFE_SAMPLES:
                        print(
                            "Final PLC zero-output verification: PASSED"
                        )
                        return

                    await asyncio.sleep(FINAL_SAFE_SAMPLE_S)

                raise RuntimeError(
                    "Final PLC zero-output verification failed."
                )

            experiment_error: BaseException | None = None

            with csv_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=fields,
                    delimiter=";",
                )
                writer.writeheader()

                try:
                    print(
                        "Waiting for a stable safe initial state "
                        "inside the approved level band..."
                    )
                    stable = 0
                    deadline = time.monotonic() + 12.0

                    while time.monotonic() < deadline:
                        state = await sample("STARTUP", writer)
                        level_raw = int(state["Nivel"])
                        valid = (
                            watchdog_ok(state)
                            and initial_level_ok(
                                level_raw,
                                config,
                            )
                            and state["Enable"] is False
                            and int(state["DAC"]) == 0
                            and state["AppliedEnable"] is False
                            and int(state["AppliedDAC"]) == 0
                        )
                        stable = stable + 1 if valid else 0

                        if stable >= 8:
                            break

                        await asyncio.sleep(0.25)

                    if stable < 8:
                        raise RuntimeError(
                            "The initial safe state and approved "
                            "level band did not stabilize."
                        )

                    await record_for(
                        "BASELINE",
                        config.baseline_s,
                        writer,
                    )

                    await write_only(
                        enable_node,
                        True,
                        ua.VariantType.Boolean,
                    )

                    deadline = time.monotonic() + 5.0

                    while time.monotonic() < deadline:
                        state = await sample("ENABLE_ON", writer)

                        if (
                            watchdog_ok(state)
                            and state["AppliedEnable"] is True
                            and int(state["AppliedDAC"]) == 0
                        ):
                            break

                        await asyncio.sleep(config.sample_s)
                    else:
                        raise RuntimeError(
                            "Enable was not applied."
                        )

                    for (
                        current_step_index,
                        current_step,
                    ) in enumerate(config.steps, start=1):
                        prefix = f"STEP_{current_step_index:02d}"
                        await write_only(
                            dac_node,
                            current_step.dac,
                            ua.VariantType.Int16,
                        )

                        deadline = time.monotonic() + 20.0

                        while time.monotonic() < deadline:
                            state = await sample(
                                f"{prefix}_RAMP",
                                writer,
                            )

                            if not watchdog_ok(state):
                                raise RuntimeError(
                                    "Watchdog failed during DAC "
                                    f"transition {current_step_index}."
                                )

                            if (
                                int(state["AppliedDAC"])
                                == current_step.dac
                            ):
                                break

                            await asyncio.sleep(config.sample_s)
                        else:
                            raise RuntimeError(
                                "Requested DAC was not reached "
                                f"for step {current_step_index}."
                            )

                        await record_for(
                            f"{prefix}_HOLD",
                            current_step.hold_s,
                            writer,
                        )

                    current_step_index = 0
                    current_step = None

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

                    await record_for(
                        "RECOVERY",
                        config.recovery_s,
                        writer,
                    )

                    print()
                    print(
                        "Multi-step open-loop sequence: PASSED"
                    )
                    print(f"CSV: {csv_path}")
                except BaseException as error:
                    experiment_error = error

                try:
                    await force_and_verify_safe_state()
                except BaseException as cleanup_error:
                    raise RuntimeError(
                        "The experiment ended without a verified "
                        "final PLC zero-output state."
                    ) from cleanup_error

                if experiment_error is not None:
                    raise experiment_error

    return csv_path


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)

    try:
        config.validate(execute=bool(args.execute))
    except ValueError as error:
        parser.error(str(error))

    if args.plan:
        print_plan(config)
        return 0

    asyncio.run(run_experiment(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
