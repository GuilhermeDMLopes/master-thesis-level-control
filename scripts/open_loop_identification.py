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
DEFAULT_TARGET_DAC = 12000
DEFAULT_BASELINE_S = 8.0
DEFAULT_HOLD_S = 20.0
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
class IdentificationConfig:
    plc_endpoint: str
    gateway_endpoint: str
    gateway_uri: str
    target_dac: int
    maximum_level_raw: int | None
    baseline_s: float
    hold_s: float
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
        if not DAC_MIN <= self.target_dac <= DAC_MAX:
            raise ValueError(
                f"Target DAC must be between {DAC_MIN} and {DAC_MAX}."
            )
        if self.maximum_level_raw is not None and self.maximum_level_raw <= 0:
            raise ValueError("Maximum raw level must be greater than zero.")
        if execute and self.maximum_level_raw is None:
            raise ValueError(
                "--maximum-level-raw is required with --execute."
            )
        if self.baseline_s < 0.0:
            raise ValueError("Baseline duration must not be negative.")
        if self.hold_s <= 0.0:
            raise ValueError("Hold duration must be greater than zero.")
        if self.recovery_s < 0.0:
            raise ValueError("Recovery duration must not be negative.")
        if self.sample_s <= 0.0:
            raise ValueError("Sampling period must be greater than zero.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect or execute the real-plant open-loop "
            "identification sequence. Network access and actuator writes "
            "occur only with --execute."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help="print the resolved experiment plan without network access",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "run the real-plant sequence after configuration validation "
            "and interactive confirmation"
        ),
    )

    parser.add_argument(
        "--plc-endpoint",
        default=DEFAULT_PLC_ENDPOINT,
        help=f"B&R PLC OPC UA endpoint (default: {DEFAULT_PLC_ENDPOINT})",
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
        help=f"gateway namespace URI (default: {DEFAULT_GATEWAY_URI})",
    )
    parser.add_argument(
        "--target-dac",
        type=int,
        default=DEFAULT_TARGET_DAC,
        help=f"open-loop DAC target (default: {DEFAULT_TARGET_DAC})",
    )
    parser.add_argument(
        "--maximum-level-raw",
        type=int,
        default=None,
        help=(
            "mandatory upper raw-level trip threshold for --execute; "
            "the sequence aborts at or above this value"
        ),
    )
    parser.add_argument(
        "--baseline-s",
        type=float,
        default=DEFAULT_BASELINE_S,
        help=f"baseline duration in seconds (default: {DEFAULT_BASELINE_S})",
    )
    parser.add_argument(
        "--hold-s",
        type=float,
        default=DEFAULT_HOLD_S,
        help=f"DAC hold duration in seconds (default: {DEFAULT_HOLD_S})",
    )
    parser.add_argument(
        "--recovery-s",
        type=float,
        default=DEFAULT_RECOVERY_S,
        help=f"recovery recording duration (default: {DEFAULT_RECOVERY_S})",
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=DEFAULT_SAMPLE_S,
        help=f"sampling period in seconds (default: {DEFAULT_SAMPLE_S})",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/raw"),
        help="root directory for raw experiment output (default: data/raw)",
    )

    return parser


def config_from_args(args: argparse.Namespace) -> IdentificationConfig:
    return IdentificationConfig(
        plc_endpoint=args.plc_endpoint,
        gateway_endpoint=args.gateway_endpoint,
        gateway_uri=args.gateway_uri,
        target_dac=args.target_dac,
        maximum_level_raw=args.maximum_level_raw,
        baseline_s=args.baseline_s,
        hold_s=args.hold_s,
        recovery_s=args.recovery_s,
        sample_s=args.sample_s,
        output_root=args.output_root,
    )


def print_plan(config: IdentificationConfig) -> None:
    maximum_level = (
        str(config.maximum_level_raw)
        if config.maximum_level_raw is not None
        else "NOT SET (required for --execute)"
    )

    print("OPEN-LOOP IDENTIFICATION PLAN")
    print("=============================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print(f"PLC endpoint: {config.plc_endpoint}")
    print(f"Gateway endpoint: {config.gateway_endpoint}")
    print(f"Gateway URI: {config.gateway_uri}")
    print(f"Target DAC: {config.target_dac}")
    print(f"Maximum raw level: {maximum_level}")
    print(f"Baseline duration: {config.baseline_s:.3f} s")
    print(f"Hold duration: {config.hold_s:.3f} s")
    print(f"Recovery duration: {config.recovery_s:.3f} s")
    print(f"Sampling period: {config.sample_s:.3f} s")
    print(f"Output root: {config.output_root}")
    print()
    print("Execution requires --execute and the confirmation token:")
    print(CONFIRMATION_TOKEN)


def watchdog_ok(state: dict[str, object]) -> bool:
    return (
        state["SafetyReset"] is False
        and state["WatchdogHealthy"] is True
        and state["WatchdogTripped"] is False
    )


async def run_experiment(config: IdentificationConfig) -> Path:
    # Importing asyncua only in execute mode keeps --help and --plan offline.
    from asyncua import Client, ua

    confirmation = input(
        "Type IDENTIFICATION_READY only after the physical stop has been "
        "released and the plant is approved for actuation: "
    ).strip()

    if confirmation != CONFIRMATION_TOKEN:
        raise RuntimeError("Experiment was not confirmed.")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = config.output_root / f"open-loop-identification-{run_id}"
    run_root.mkdir(parents=True, exist_ok=False)
    csv_path = run_root / "open-loop-identification.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "level_raw",
        "target_dac",
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

    async def write_only(node, value, variant_type) -> None:
        await node.write_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(ua.Variant(value, variant_type)),
        )

    async def read_plc(client) -> dict[str, object]:
        return {
            name: await client.get_node(node_id).read_value()
            for name, node_id in PLC_IDS.items()
        }

    async with Client(config.plc_endpoint, timeout=5.0) as plc:
        async with Client(config.gateway_endpoint, timeout=5.0) as gateway:
            namespace_index = await gateway.get_namespace_index(
                config.gateway_uri
            )
            enable_node = gateway.get_node(
                ua.NodeId("Enable", namespace_index)
            )
            dac_node = gateway.get_node(ua.NodeId("DAC", namespace_index))

            async def sample(phase: str, writer: csv.DictWriter):
                nonlocal last_print

                state = await read_plc(plc)
                gateway_enable = await enable_node.read_value()
                gateway_dac = await dac_node.read_value()
                level_raw = int(state["Nivel"])

                writer.writerow(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "elapsed_s": round(time.monotonic() - start, 6),
                        "phase": phase,
                        "level_raw": level_raw,
                        "target_dac": config.target_dac,
                        "maximum_level_raw": config.maximum_level_raw,
                        "heartbeat": int(state["Heartbeat"]),
                        "watchdog_healthy": bool(state["WatchdogHealthy"]),
                        "watchdog_tripped": bool(state["WatchdogTripped"]),
                        "safety_reset": bool(state["SafetyReset"]),
                        "enable_plc": bool(state["Enable"]),
                        "dac_plc": int(state["DAC"]),
                        "applied_enable": bool(state["AppliedEnable"]),
                        "applied_dac": int(state["AppliedDAC"]),
                        "gateway_enable_request": bool(gateway_enable),
                        "gateway_dac_request": int(gateway_dac),
                    }
                )

                if level_raw >= int(config.maximum_level_raw):
                    raise RuntimeError(
                        "Maximum raw-level threshold reached: "
                        f"{level_raw} >= {config.maximum_level_raw}."
                    )

                now = time.monotonic()
                if now - last_print >= 0.5:
                    print(
                        f"{phase:12s} | "
                        f"t={now-start:6.2f}s | "
                        f"Nivel={level_raw:5d} | "
                        f"Healthy={state['WatchdogHealthy']} | "
                        f"Tripped={state['WatchdogTripped']} | "
                        f"Enable={state['Enable']} | "
                        f"DAC={int(state['DAC']):5d} | "
                        f"AppliedDAC={int(state['AppliedDAC']):5d}"
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
                deadline = time.monotonic() + duration_s

                while time.monotonic() < deadline:
                    state = await sample(phase, writer)
                    if require_watchdog and not watchdog_ok(state):
                        raise RuntimeError(
                            f"Watchdog was invalid during {phase}."
                        )
                    await asyncio.sleep(config.sample_s)

            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=fields,
                    delimiter=";",
                )
                writer.writeheader()

                try:
                    print("Waiting for a stable safe initial state...")
                    stable = 0
                    deadline = time.monotonic() + 12.0

                    while time.monotonic() < deadline:
                        state = await sample("STARTUP", writer)
                        valid = (
                            watchdog_ok(state)
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
                            "The initial safe state did not stabilize."
                        )

                    print("Recording baseline...")
                    await record_for("BASELINE", config.baseline_s, writer)

                    print("Requesting Enable=True with DAC=0...")
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
                        raise RuntimeError("Enable was not applied.")

                    print(f"Requesting DAC={config.target_dac}...")
                    await write_only(
                        dac_node,
                        config.target_dac,
                        ua.VariantType.Int16,
                    )

                    deadline = time.monotonic() + 20.0
                    while time.monotonic() < deadline:
                        state = await sample("RAMP_UP", writer)
                        if not watchdog_ok(state):
                            raise RuntimeError(
                                "Watchdog failed during the DAC ramp."
                            )
                        if int(state["AppliedDAC"]) == config.target_dac:
                            break
                        await asyncio.sleep(config.sample_s)
                    else:
                        raise RuntimeError(
                            f"DAC {config.target_dac} was not reached."
                        )

                    print(
                        f"DAC {config.target_dac} reached. "
                        f"Holding for {config.hold_s:.3f} seconds..."
                    )
                    await record_for("HOLD", config.hold_s, writer)

                    print("Disabling output immediately with Enable=False...")
                    shutdown_start = time.monotonic()
                    await write_only(
                        enable_node,
                        False,
                        ua.VariantType.Boolean,
                    )

                    deadline = time.monotonic() + 3.0
                    while time.monotonic() < deadline:
                        state = await sample("ENABLE_OFF", writer)
                        if (
                            state["AppliedEnable"] is False
                            and int(state["AppliedDAC"]) == 0
                        ):
                            break
                        await asyncio.sleep(config.sample_s)
                    else:
                        raise RuntimeError("Applied output was not removed.")

                    print(
                        "Applied output removed in "
                        f"{time.monotonic()-shutdown_start:.3f} s"
                    )
                    await write_only(
                        dac_node,
                        0,
                        ua.VariantType.Int16,
                    )

                    print("Recording recovery...")
                    await record_for("RECOVERY", config.recovery_s, writer)

                    print()
                    print("Open-loop identification sequence: PASSED")
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
                        print("Final safe commands written.")
                    except Exception as error:
                        print(f"Cleanup warning: {error!r}")

    return csv_path


def main(argv: Sequence[str] | None = None) -> int:
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
