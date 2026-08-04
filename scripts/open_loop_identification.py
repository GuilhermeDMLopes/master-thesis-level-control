from __future__ import annotations

import argparse
import asyncio
import csv
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


DEFAULT_PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
DEFAULT_GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
DEFAULT_GATEWAY_URI = "urn:br-4diac-gateway"
DEFAULT_BASELINE_S = 8.0
DEFAULT_RECOVERY_S = 10.0
DEFAULT_SAMPLE_S = 0.10
DAC_MIN = 0
DAC_MAX = 32000
CONFIRMATION_TOKEN = "IDENTIFICATION_READY"

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
    baseline_s: float
    recovery_s: float
    sample_s: float
    output_root: Path

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

        optional_positive_values = (
            (
                "Initial minimum raw level",
                self.initial_level_min_raw,
            ),
            (
                "Initial maximum raw level",
                self.initial_level_max_raw,
            ),
            (
                "Maximum raw level",
                self.maximum_level_raw,
            ),
        )

        for name, value in optional_positive_values:
            if value is not None and value < 0:
                raise ValueError(
                    f"{name} must not be negative."
                )

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

    step = ExcitationStep(
        dac=dac,
        hold_s=hold_s,
    )

    try:
        step.validate()
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            str(error)
        ) from error

    return step


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect or execute a multi-step real-plant "
            "open-loop identification sequence. Network access "
            "and actuator writes occur only with --execute. "
            "No excitation DAC values are supplied by default."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help=(
            "print the resolved experiment plan without "
            "network access"
        ),
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "run the real-plant sequence after configuration "
            "validation and interactive confirmation"
        ),
    )

    parser.add_argument(
        "--plc-endpoint",
        default=DEFAULT_PLC_ENDPOINT,
        help=(
            "B&R PLC OPC UA endpoint "
            f"(default: {DEFAULT_PLC_ENDPOINT})"
        ),
    )
    parser.add_argument(
        "--gateway-endpoint",
        default=DEFAULT_GATEWAY_ENDPOINT,
        help=(
            "Python gateway OPC UA endpoint "
            f"(default: {DEFAULT_GATEWAY_ENDPOINT})"
        ),
    )
    parser.add_argument(
        "--gateway-uri",
        default=DEFAULT_GATEWAY_URI,
        help=(
            "gateway namespace URI "
            f"(default: {DEFAULT_GATEWAY_URI})"
        ),
    )
    parser.add_argument(
        "--dac-step",
        type=parse_dac_step,
        action="append",
        default=[],
        metavar="DAC:HOLD_S",
        help=(
            "append one explicitly reviewed positive-DAC "
            "plateau and hold duration; repeat this option "
            "to build the sequence"
        ),
    )
    parser.add_argument(
        "--initial-level-min-raw",
        type=int,
        default=None,
        help=(
            "mandatory lower raw-level bound for the stable "
            "initial state in --execute mode"
        ),
    )
    parser.add_argument(
        "--initial-level-max-raw",
        type=int,
        default=None,
        help=(
            "mandatory upper raw-level bound for the stable "
            "initial state in --execute mode"
        ),
    )
    parser.add_argument(
        "--maximum-level-raw",
        type=int,
        default=None,
        help=(
            "mandatory upper raw-level trip threshold for "
            "--execute; the sequence aborts at or above it"
        ),
    )
    parser.add_argument(
        "--baseline-s",
        type=float,
        default=DEFAULT_BASELINE_S,
        help=(
            "zero-output baseline duration in seconds "
            f"(default: {DEFAULT_BASELINE_S})"
        ),
    )
    parser.add_argument(
        "--recovery-s",
        type=float,
        default=DEFAULT_RECOVERY_S,
        help=(
            "zero-output recovery duration in seconds "
            f"(default: {DEFAULT_RECOVERY_S})"
        ),
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=DEFAULT_SAMPLE_S,
        help=(
            "sampling period in seconds "
            f"(default: {DEFAULT_SAMPLE_S})"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/raw"),
        help=(
            "root directory for raw experiment output "
            "(default: data/raw)"
        ),
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
        baseline_s=args.baseline_s,
        recovery_s=args.recovery_s,
        sample_s=args.sample_s,
        output_root=args.output_root,
    )


def optional_value(
    value: int | None,
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
        for index, step in enumerate(
            config.steps,
            start=1,
        ):
            print(
                f"  step {index}: DAC={step.dac}, "
                f"hold={step.hold_s:.3f} s"
            )
        print(
            "Total positive-DAC hold time: "
            f"{sum(step.hold_s for step in config.steps):.3f} s"
        )
    else:
        print(
            "DAC sequence: NOT SET "
            "(at least one --dac-step is required for --execute)"
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
        f"Baseline duration: {config.baseline_s:.3f} s"
    )
    print(
        f"Recovery duration: {config.recovery_s:.3f} s"
    )
    print(
        f"Sampling period: {config.sample_s:.3f} s"
    )
    print(f"Output root: {config.output_root}")
    print()
    print(
        "Execution requires --execute, all required "
        "limits, at least one --dac-step, and the token:"
    )
    print(CONFIRMATION_TOKEN)


def watchdog_ok(
    state: dict[str, object],
) -> bool:
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
    # Keeping this import inside execute mode prevents --help,
    # --plan, and module import from accessing OPC UA.
    from asyncua import Client, ua

    confirmation = input(
        "Type IDENTIFICATION_READY only after the physical "
        "stop has been released and the reviewed multi-step "
        "plan is approved for real-plant actuation: "
    ).strip()

    if confirmation != CONFIRMATION_TOKEN:
        raise RuntimeError(
            "Experiment was not confirmed."
        )

    assert config.steps
    assert config.initial_level_min_raw is not None
    assert config.initial_level_max_raw is not None
    assert config.maximum_level_raw is not None

    run_id = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    run_root = (
        config.output_root
        / f"open-loop-identification-{run_id}"
    )
    run_root.mkdir(
        parents=True,
        exist_ok=False,
    )
    csv_path = (
        run_root
        / "open-loop-identification.csv"
    )

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "step_index",
        "step_dac",
        "step_hold_s",
        "level_raw",
        "initial_level_min_raw",
        "initial_level_max_raw",
        "maximum_level_raw",
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

    async def read_plc(
        client,
    ) -> dict[str, object]:
        return {
            name: (
                await client.get_node(
                    node_id
                ).read_value()
            )
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
            namespace_index = (
                await gateway.get_namespace_index(
                    config.gateway_uri
                )
            )
            enable_node = gateway.get_node(
                ua.NodeId(
                    "Enable",
                    namespace_index,
                )
            )
            dac_node = gateway.get_node(
                ua.NodeId(
                    "DAC",
                    namespace_index,
                )
            )

            async def sample(
                phase: str,
                writer: csv.DictWriter,
            ) -> dict[str, object]:
                nonlocal last_print

                state = await read_plc(plc)
                gateway_enable = (
                    await enable_node.read_value()
                )
                gateway_dac = (
                    await dac_node.read_value()
                )
                level_raw = int(state["Nivel"])

                writer.writerow(
                    {
                        "timestamp": (
                            datetime.now().isoformat()
                        ),
                        "elapsed_s": round(
                            time.monotonic() - start,
                            6,
                        ),
                        "phase": phase,
                        "step_index": (
                            current_step_index
                        ),
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
                        "initial_level_min_raw": (
                            config.initial_level_min_raw
                        ),
                        "initial_level_max_raw": (
                            config.initial_level_max_raw
                        ),
                        "maximum_level_raw": (
                            config.maximum_level_raw
                        ),
                        "heartbeat": int(
                            state["Heartbeat"]
                        ),
                        "watchdog_healthy": bool(
                            state["WatchdogHealthy"]
                        ),
                        "watchdog_tripped": bool(
                            state["WatchdogTripped"]
                        ),
                        "safety_reset": bool(
                            state["SafetyReset"]
                        ),
                        "enable_plc": bool(
                            state["Enable"]
                        ),
                        "dac_plc": int(
                            state["DAC"]
                        ),
                        "applied_enable": bool(
                            state["AppliedEnable"]
                        ),
                        "applied_dac": int(
                            state["AppliedDAC"]
                        ),
                        "gateway_enable_request": bool(
                            gateway_enable
                        ),
                        "gateway_dac_request": int(
                            gateway_dac
                        ),
                    }
                )

                if (
                    level_raw
                    >= config.maximum_level_raw
                ):
                    raise RuntimeError(
                        "Maximum raw-level threshold "
                        "reached: "
                        f"{level_raw} >= "
                        f"{config.maximum_level_raw}."
                    )

                now = time.monotonic()

                if now - last_print >= 0.5:
                    print(
                        f"{phase:16s} | "
                        f"t={now-start:7.2f}s | "
                        f"Nivel={level_raw:5d} | "
                        f"Healthy="
                        f"{state['WatchdogHealthy']} | "
                        f"Tripped="
                        f"{state['WatchdogTripped']} | "
                        f"AppliedDAC="
                        f"{int(state['AppliedDAC']):5d}"
                    )
                    last_print = now

                return state

            async def record_for(
                phase: str,
                duration_s: float,
                writer: csv.DictWriter,
                *,
                require_watchdog: bool = True,
            ) -> None:
                deadline = (
                    time.monotonic()
                    + duration_s
                )

                while (
                    time.monotonic()
                    < deadline
                ):
                    state = await sample(
                        phase,
                        writer,
                    )

                    if (
                        require_watchdog
                        and not watchdog_ok(state)
                    ):
                        raise RuntimeError(
                            "Watchdog was invalid "
                            f"during {phase}."
                        )

                    await asyncio.sleep(
                        config.sample_s
                    )

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
                        "Waiting for a stable safe "
                        "initial state within the "
                        "approved raw-level band..."
                    )
                    stable = 0
                    deadline = (
                        time.monotonic()
                        + 12.0
                    )

                    while (
                        time.monotonic()
                        < deadline
                    ):
                        state = await sample(
                            "STARTUP",
                            writer,
                        )
                        level_raw = int(
                            state["Nivel"]
                        )
                        valid = (
                            watchdog_ok(state)
                            and initial_level_ok(
                                level_raw,
                                config,
                            )
                            and state["Enable"] is False
                            and int(state["DAC"]) == 0
                            and (
                                state["AppliedEnable"]
                                is False
                            )
                            and (
                                int(state["AppliedDAC"])
                                == 0
                            )
                        )
                        stable = (
                            stable + 1
                            if valid
                            else 0
                        )

                        if stable >= 8:
                            break

                        await asyncio.sleep(0.25)

                    if stable < 8:
                        raise RuntimeError(
                            "The initial safe state "
                            "and approved level band "
                            "did not stabilize."
                        )

                    print(
                        "Recording zero-output baseline..."
                    )
                    await record_for(
                        "BASELINE",
                        config.baseline_s,
                        writer,
                    )

                    print(
                        "Requesting Enable=True "
                        "with DAC=0..."
                    )
                    await write_only(
                        enable_node,
                        True,
                        ua.VariantType.Boolean,
                    )

                    deadline = (
                        time.monotonic()
                        + 5.0
                    )

                    while (
                        time.monotonic()
                        < deadline
                    ):
                        state = await sample(
                            "ENABLE_ON",
                            writer,
                        )

                        if (
                            watchdog_ok(state)
                            and (
                                state["AppliedEnable"]
                                is True
                            )
                            and (
                                int(state["AppliedDAC"])
                                == 0
                            )
                        ):
                            break

                        await asyncio.sleep(
                            config.sample_s
                        )
                    else:
                        raise RuntimeError(
                            "Enable was not applied."
                        )

                    for (
                        current_step_index,
                        current_step,
                    ) in enumerate(
                        config.steps,
                        start=1,
                    ):
                        step_prefix = (
                            f"STEP_"
                            f"{current_step_index:02d}"
                        )
                        print(
                            f"Requesting step "
                            f"{current_step_index}: "
                            f"DAC={current_step.dac}..."
                        )
                        await write_only(
                            dac_node,
                            current_step.dac,
                            ua.VariantType.Int16,
                        )

                        deadline = (
                            time.monotonic()
                            + 20.0
                        )

                        while (
                            time.monotonic()
                            < deadline
                        ):
                            state = await sample(
                                f"{step_prefix}_RAMP",
                                writer,
                            )

                            if not watchdog_ok(
                                state
                            ):
                                raise RuntimeError(
                                    "Watchdog failed "
                                    "during the DAC "
                                    f"transition for "
                                    f"step "
                                    f"{current_step_index}."
                                )

                            if (
                                int(
                                    state[
                                        "AppliedDAC"
                                    ]
                                )
                                == current_step.dac
                            ):
                                break

                            await asyncio.sleep(
                                config.sample_s
                            )
                        else:
                            raise RuntimeError(
                                "Requested DAC was not "
                                "reached for step "
                                f"{current_step_index}: "
                                f"{current_step.dac}."
                            )

                        print(
                            f"Step "
                            f"{current_step_index} "
                            f"reached. Holding for "
                            f"{current_step.hold_s:.3f} "
                            "seconds..."
                        )
                        await record_for(
                            f"{step_prefix}_HOLD",
                            current_step.hold_s,
                            writer,
                        )

                    current_step_index = 0
                    current_step = None

                    print(
                        "Disabling output immediately "
                        "with Enable=False..."
                    )
                    shutdown_start = (
                        time.monotonic()
                    )
                    await write_only(
                        enable_node,
                        False,
                        ua.VariantType.Boolean,
                    )

                    deadline = (
                        time.monotonic()
                        + 3.0
                    )

                    while (
                        time.monotonic()
                        < deadline
                    ):
                        state = await sample(
                            "ENABLE_OFF",
                            writer,
                        )

                        if (
                            state["AppliedEnable"]
                            is False
                            and (
                                int(
                                    state[
                                        "AppliedDAC"
                                    ]
                                )
                                == 0
                            )
                        ):
                            break

                        await asyncio.sleep(
                            config.sample_s
                        )
                    else:
                        raise RuntimeError(
                            "Applied output was not "
                            "removed."
                        )

                    print(
                        "Applied output removed in "
                        f"{time.monotonic()-shutdown_start:.3f} s"
                    )
                    await write_only(
                        dac_node,
                        0,
                        ua.VariantType.Int16,
                    )

                    print(
                        "Recording zero-output recovery..."
                    )
                    await record_for(
                        "RECOVERY",
                        config.recovery_s,
                        writer,
                    )

                    print()
                    print(
                        "Multi-step open-loop "
                        "identification sequence: PASSED"
                    )
                    print(f"CSV: {csv_path}")
                finally:
                    try:
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
                        await asyncio.sleep(0.8)
                        print(
                            "Final safe commands written."
                        )
                    except Exception as error:
                        print(
                            "Cleanup warning: "
                            f"{error!r}"
                        )

    return csv_path


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)

    try:
        config.validate(
            execute=bool(args.execute)
        )
    except ValueError as error:
        parser.error(str(error))

    if args.plan:
        print_plan(config)
        return 0

    asyncio.run(
        run_experiment(config)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
