from __future__ import annotations

import argparse
import asyncio
import csv
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


DEFAULT_PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
CONFIRMATION_TOKEN = "OBSERVATION_READY"

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
class ObservationConfig:
    plc_endpoint: str
    label: str | None
    duration_s: float | None
    sample_s: float
    output_root: Path

    def validate(self, *, observe: bool) -> None:
        if not self.plc_endpoint.strip():
            raise ValueError("PLC endpoint must not be empty.")

        if observe and not self.label:
            raise ValueError("--label is required with --observe.")

        if observe and self.duration_s is None:
            raise ValueError("--duration-s is required with --observe.")

        if self.duration_s is not None and self.duration_s <= 0.0:
            raise ValueError(
                "Observation duration must be greater than zero."
            )

        if self.sample_s <= 0.0:
            raise ValueError(
                "Sampling period must be greater than zero."
            )

        if (
            self.duration_s is not None
            and self.duration_s < self.sample_s * 5.0
        ):
            raise ValueError(
                "Observation duration must contain at least "
                "five sampling periods."
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or perform a read-only real-plant PLC "
            "observation. The tool never connects to the gateway "
            "and contains no OPC UA write operation."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help="print the read-only plan without network access",
    )
    mode.add_argument(
        "--observe",
        action="store_true",
        help=(
            "connect to the PLC and record only while command "
            "and applied output remain zero"
        ),
    )

    parser.add_argument(
        "--plc-endpoint",
        default=DEFAULT_PLC_ENDPOINT,
    )
    parser.add_argument(
        "--label",
        default=None,
        help=(
            "explicit observation label, for example "
            "empty-tank or initial-band"
        ),
    )
    parser.add_argument(
        "--duration-s",
        type=float,
        default=None,
        help="mandatory observation duration with --observe",
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/raw"),
    )

    return parser


def config_from_args(
    args: argparse.Namespace,
) -> ObservationConfig:
    return ObservationConfig(
        plc_endpoint=args.plc_endpoint,
        label=args.label,
        duration_s=args.duration_s,
        sample_s=args.sample_s,
        output_root=args.output_root,
    )


def print_plan(config: ObservationConfig) -> None:
    print("READ-ONLY PLANT OBSERVATION PLAN")
    print("================================")
    print("NETWORK ACCESS: NO")
    print("OPC UA WRITES: NO")
    print("GATEWAY CONNECTION: NO")
    print("FORTE REQUIRED: NO")
    print(f"PLC endpoint: {config.plc_endpoint}")
    print(
        "Label: "
        + (
            config.label
            if config.label is not None
            else "NOT SET (required for --observe)"
        )
    )
    print(
        "Duration: "
        + (
            f"{config.duration_s:.3f} s"
            if config.duration_s is not None
            else "NOT SET (required for --observe)"
        )
    )
    print(f"Sampling period: {config.sample_s:.3f} s")
    print(f"Output root: {config.output_root}")
    print()
    print("Observation requires the token:")
    print(CONFIRMATION_TOKEN)


def zero_output_state(state: dict[str, object]) -> bool:
    return (
        state["Enable"] is False
        and int(state["DAC"]) == 0
        and state["AppliedEnable"] is False
        and int(state["AppliedDAC"]) == 0
    )


def summarize_levels(
    levels: Sequence[int],
) -> dict[str, float]:
    if not levels:
        raise ValueError("No level samples were recorded.")

    return {
        "minimum": float(min(levels)),
        "maximum": float(max(levels)),
        "median": float(statistics.median(levels)),
        "mean": float(statistics.fmean(levels)),
        "peak_to_peak": float(max(levels) - min(levels)),
    }


async def run_observation(
    config: ObservationConfig,
) -> Path:
    # The import remains inside observe mode so --help, --plan,
    # and module import remain fully offline.
    from asyncua import Client

    confirmation = input(
        "Type OBSERVATION_READY only after confirming that "
        "the pump must remain off and no controller or gateway "
        "process is running: "
    ).strip()

    if confirmation != CONFIRMATION_TOKEN:
        raise RuntimeError("Observation was not confirmed.")

    assert config.label is not None
    assert config.duration_s is not None

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = "".join(
        character
        if character.isalnum() or character in {"-", "_"}
        else "-"
        for character in config.label.strip()
    ).strip("-")

    if not safe_label:
        raise RuntimeError("Observation label is empty after normalization.")

    run_root = (
        config.output_root
        / f"plant-observation-{safe_label}-{run_id}"
    )
    run_root.mkdir(parents=True, exist_ok=False)
    csv_path = run_root / "plant-observation.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "label",
        "level_raw",
        "heartbeat",
        "watchdog_healthy",
        "watchdog_tripped",
        "safety_reset",
        "enable",
        "dac",
        "applied_enable",
        "applied_dac",
    ]

    levels: list[int] = []
    start = time.monotonic()

    async with Client(
        config.plc_endpoint,
        timeout=5.0,
    ) as plc:
        nodes = {
            name: plc.get_node(node_id)
            for name, node_id in PLC_IDS.items()
        }

        async def read_state() -> dict[str, object]:
            return {
                name: await node.read_value()
                for name, node in nodes.items()
            }

        # Require a stable zero-output state before recording.
        stable = 0
        deadline = time.monotonic() + 5.0

        while time.monotonic() < deadline:
            state = await read_state()
            stable = stable + 1 if zero_output_state(state) else 0

            if stable >= 5:
                break

            await asyncio.sleep(0.2)

        if stable < 5:
            raise RuntimeError(
                "PLC command and applied output did not remain "
                "zero for five consecutive preflight samples."
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

            deadline = time.monotonic() + config.duration_s

            while time.monotonic() < deadline:
                state = await read_state()

                if not zero_output_state(state):
                    raise RuntimeError(
                        "Observation aborted because command or "
                        "applied output became non-zero."
                    )

                level_raw = int(state["Nivel"])
                elapsed_s = time.monotonic() - start
                levels.append(level_raw)

                writer.writerow(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "elapsed_s": round(elapsed_s, 6),
                        "label": config.label,
                        "level_raw": level_raw,
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
                        "enable": bool(state["Enable"]),
                        "dac": int(state["DAC"]),
                        "applied_enable": bool(
                            state["AppliedEnable"]
                        ),
                        "applied_dac": int(
                            state["AppliedDAC"]
                        ),
                    }
                )
                stream.flush()
                await asyncio.sleep(config.sample_s)

        final_state = await read_state()

        if not zero_output_state(final_state):
            raise RuntimeError(
                "Final PLC state was not zero output."
            )

    summary = summarize_levels(levels)

    print()
    print("READ-ONLY OBSERVATION COMPLETED")
    print("===============================")
    print(f"Samples: {len(levels)}")
    print(
        "Raw level range: "
        f"{summary['minimum']:.0f} to "
        f"{summary['maximum']:.0f}"
    )
    print(f"Raw level median: {summary['median']:.3f}")
    print(f"Raw level mean: {summary['mean']:.3f}")
    print(
        "Raw level peak-to-peak: "
        f"{summary['peak_to_peak']:.3f}"
    )
    print("OPC UA WRITES: NO")
    print("FINAL ZERO OUTPUT: YES")
    print(f"CSV: {csv_path}")

    return csv_path


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)

    try:
        config.validate(observe=bool(args.observe))
    except ValueError as error:
        parser.error(str(error))

    if args.plan:
        print_plan(config)
        return 0

    asyncio.run(run_observation(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
