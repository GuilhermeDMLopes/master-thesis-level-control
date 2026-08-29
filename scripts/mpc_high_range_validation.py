from __future__ import annotations

import argparse
import asyncio
import csv
import math
import statistics
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from asyncua import Client, ua


DEFAULT_GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
DEFAULT_GATEWAY_URI = "urn:br-4diac-gateway"
DEFAULT_PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
DEFAULT_OUTPUT_ROOT = Path("data/raw")

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

CONFIRMATION_TOKEN = "HIGH_RANGE_MPC_READY"


@dataclass(frozen=True)
class GatewayNodes:
    nivel: object
    enable: object
    dac: object
    applied_enable: object
    applied_dac: object
    watchdog_healthy: object


@dataclass(frozen=True)
class PlcNodes:
    nivel: object
    enable: object
    dac: object
    applied_enable: object
    applied_dac: object
    watchdog_healthy: object
    watchdog_tripped: object


def finite_number(value: object) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"non-finite numeric value observed: {value!r}")
    return number


def bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise RuntimeError(f"unexpected BOOL-compatible value: {value!r}")


def is_zero(value: object) -> bool:
    return abs(finite_number(value)) <= 1e-9


async def write_value_only(
    node: object,
    value: object,
    variant_type: ua.VariantType,
) -> None:
    """Write only the OPC UA Value attribute.

    The real B&R server rejects writes that include unsupported
    status/timestamp combinations.
    """
    variant = ua.Variant(value, variant_type)
    data_value = ua.DataValue(variant)
    await node.write_attribute(
        ua.AttributeIds.Value,
        data_value,
    )


async def resolve_gateway_nodes(
    client: Client,
    namespace_uri: str,
) -> GatewayNodes:
    namespace_index = await client.get_namespace_index(namespace_uri)

    def node(name: str):
        return client.get_node(
            ua.NodeId(name, namespace_index, ua.NodeIdType.String)
        )

    nodes = GatewayNodes(
        nivel=node("Nivel"),
        enable=node("Enable"),
        dac=node("DAC"),
        applied_enable=node("AppliedEnable"),
        applied_dac=node("AppliedDAC"),
        watchdog_healthy=node("WatchdogHealthy"),
    )

    for label, target in (
        ("Nivel", nodes.nivel),
        ("Enable", nodes.enable),
        ("DAC", nodes.dac),
        ("AppliedEnable", nodes.applied_enable),
        ("AppliedDAC", nodes.applied_dac),
        ("WatchdogHealthy", nodes.watchdog_healthy),
    ):
        try:
            await target.read_value()
        except Exception as exc:
            raise RuntimeError(
                f"gateway node {label!r} is not readable"
            ) from exc

    return nodes


async def resolve_plc_nodes(client: Client) -> PlcNodes:
    nodes = PlcNodes(
        nivel=client.get_node(PLC_IDS["Nivel"]),
        enable=client.get_node(PLC_IDS["Enable"]),
        dac=client.get_node(PLC_IDS["DAC"]),
        applied_enable=client.get_node(PLC_IDS["AppliedEnable"]),
        applied_dac=client.get_node(PLC_IDS["AppliedDAC"]),
        watchdog_healthy=client.get_node(PLC_IDS["WatchdogHealthy"]),
        watchdog_tripped=client.get_node(PLC_IDS["WatchdogTripped"]),
    )

    for label, target in (
        ("Nivel", nodes.nivel),
        ("Enable", nodes.enable),
        ("DAC", nodes.dac),
        ("AppliedEnable", nodes.applied_enable),
        ("AppliedDAC", nodes.applied_dac),
        ("WatchdogHealthy", nodes.watchdog_healthy),
        ("WatchdogTripped", nodes.watchdog_tripped),
    ):
        try:
            await target.read_value()
        except Exception as exc:
            raise RuntimeError(
                f"PLC node {label!r} is not readable"
            ) from exc

    return nodes


async def read_snapshot(
    gateway: GatewayNodes,
    plc: PlcNodes,
) -> dict[str, object]:
    values = await asyncio.gather(
        gateway.nivel.read_value(),
        gateway.enable.read_value(),
        gateway.dac.read_value(),
        gateway.applied_enable.read_value(),
        gateway.applied_dac.read_value(),
        gateway.watchdog_healthy.read_value(),
        plc.nivel.read_value(),
        plc.enable.read_value(),
        plc.dac.read_value(),
        plc.applied_enable.read_value(),
        plc.applied_dac.read_value(),
        plc.watchdog_healthy.read_value(),
        plc.watchdog_tripped.read_value(),
    )

    return {
        "gw_nivel": finite_number(values[0]),
        "gw_enable": bool_value(values[1]),
        "gw_dac": finite_number(values[2]),
        "gw_applied_enable": bool_value(values[3]),
        "gw_applied_dac": finite_number(values[4]),
        "gw_watchdog_healthy": bool_value(values[5]),
        "plc_nivel": finite_number(values[6]),
        "plc_enable": bool_value(values[7]),
        "plc_dac": finite_number(values[8]),
        "plc_applied_enable": bool_value(values[9]),
        "plc_applied_dac": finite_number(values[10]),
        "plc_watchdog_healthy": bool_value(values[11]),
        "plc_watchdog_tripped": bool_value(values[12]),
    }


def assert_initial_safe(
    snapshot: dict[str, object],
    initial_min_raw: float,
    initial_max_raw: float,
) -> None:
    failures: list[str] = []

    if not (initial_min_raw <= snapshot["gw_nivel"] <= initial_max_raw):
        failures.append(
            "initial gateway level outside approved band: "
            f"{snapshot['gw_nivel']:.1f}"
        )

    for key, expected in (
        ("gw_enable", False),
        ("gw_applied_enable", False),
        ("plc_enable", False),
        ("plc_applied_enable", False),
        ("gw_watchdog_healthy", True),
        ("plc_watchdog_healthy", True),
        ("plc_watchdog_tripped", False),
    ):
        if snapshot[key] is not expected:
            failures.append(f"{key}={snapshot[key]!r}")

    for key in (
        "gw_dac",
        "gw_applied_dac",
        "plc_dac",
        "plc_applied_dac",
    ):
        if not is_zero(snapshot[key]):
            failures.append(f"{key}={snapshot[key]!r}")

    if failures:
        raise RuntimeError(
            "INITIAL ACTIVE-COMMISSIONING PRECONDITION FAILED: "
            + "; ".join(failures)
        )


def assert_active_limits(
    snapshot: dict[str, object],
    median_raw: float,
    positive_rate_raw_per_s: float,
    *,
    maximum_median_raw: float,
    maximum_instant_raw: float,
    maximum_rate_raw_per_s: float,
    maximum_dac: float,
) -> None:
    failures: list[str] = []

    if snapshot["gw_watchdog_healthy"] is not True:
        failures.append("gateway WatchdogHealthy=False")
    if snapshot["plc_watchdog_healthy"] is not True:
        failures.append("PLC WatchdogHealthy=False")
    if snapshot["plc_watchdog_tripped"] is not False:
        failures.append("PLC WatchdogTripped=True")

    if snapshot["gw_nivel"] >= maximum_instant_raw:
        failures.append(
            f"instant raw level {snapshot['gw_nivel']:.1f} "
            f">= {maximum_instant_raw:.1f}"
        )

    if median_raw >= maximum_median_raw:
        failures.append(
            f"rolling-median raw level {median_raw:.1f} "
            f">= {maximum_median_raw:.1f}"
        )

    if positive_rate_raw_per_s >= maximum_rate_raw_per_s:
        failures.append(
            "positive rolling-median level rate "
            f"{positive_rate_raw_per_s:.1f} raw/s "
            f">= {maximum_rate_raw_per_s:.1f} raw/s"
        )

    for key in (
        "gw_dac",
        "gw_applied_dac",
        "plc_dac",
        "plc_applied_dac",
    ):
        if snapshot[key] < -1e-9:
            failures.append(f"{key} is negative: {snapshot[key]!r}")
        if snapshot[key] > maximum_dac + 1e-9:
            failures.append(
                f"{key}={snapshot[key]:.1f} exceeds DAC ceiling "
                f"{maximum_dac:.1f}"
            )

    if failures:
        raise RuntimeError(
            "ACTIVE MPC SAFETY LIMIT VIOLATION: "
            + "; ".join(failures)
        )


def terminate_forte(pid: int) -> None:
    result = subprocess.run(
        [
            "taskkill",
            "/PID",
            str(pid),
            "/F",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode not in (0, 128):
        raise RuntimeError(
            "could not terminate FORTE process "
            f"{pid}: {result.stdout} {result.stderr}"
        )


async def force_zero_outputs(
    gateway: GatewayNodes,
    plc: PlcNodes,
) -> None:
    # These are the ONLY actuator writes performed by this supervisor.
    # They always request the safe zero-output state.
    await write_value_only(
        gateway.enable,
        False,
        ua.VariantType.Boolean,
    )
    await write_value_only(
        gateway.dac,
        0,
        ua.VariantType.Int16,
    )

    # Direct PLC writes are a defense-in-depth fallback after FORTE is stopped.
    await write_value_only(
        plc.enable,
        False,
        ua.VariantType.Boolean,
    )
    await write_value_only(
        plc.dac,
        0,
        ua.VariantType.Int16,
    )


async def verify_final_zero(
    gateway: GatewayNodes,
    plc: PlcNodes,
    timeout_s: float,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_s
    last: dict[str, object] | None = None

    while time.monotonic() < deadline:
        last = await read_snapshot(gateway, plc)

        safe = (
            last["gw_enable"] is False
            and is_zero(last["gw_dac"])
            and last["gw_applied_enable"] is False
            and is_zero(last["gw_applied_dac"])
            and last["plc_enable"] is False
            and is_zero(last["plc_dac"])
            and last["plc_applied_enable"] is False
            and is_zero(last["plc_applied_dac"])
        )

        if safe:
            return last

        await asyncio.sleep(0.1)

    raise RuntimeError(
        "FINAL ZERO-OUTPUT VERIFICATION FAILED: "
        f"last snapshot={last!r}"
    )


async def safe_shutdown(
    *,
    forte_pid: int,
    gateway: GatewayNodes,
    plc: PlcNodes,
    zero_timeout_s: float,
    reason: str,
) -> dict[str, object]:
    print()
    print("SAFE SHUTDOWN")
    print("=============")
    print(f"Reason: {reason}")

    terminate_error: Exception | None = None

    try:
        terminate_forte(forte_pid)
        print(f"FORTE PID {forte_pid}: termination requested")
    except Exception as exc:
        terminate_error = exc
        print(f"WARNING: FORTE termination failed: {exc}")

    write_errors: list[str] = []

    try:
        await force_zero_outputs(gateway, plc)
        print("Gateway + PLC zero-output commands: SENT")
    except Exception as exc:
        write_errors.append(str(exc))
        print(f"WARNING: zero-output write failure: {exc}")

    final = await verify_final_zero(
        gateway,
        plc,
        timeout_s=zero_timeout_s,
    )

    print("FINAL Enable=False: YES")
    print("FINAL DAC=0: YES")
    print("FINAL AppliedEnable=False: YES")
    print("FINAL AppliedDAC=0: YES")

    if terminate_error is not None:
        raise RuntimeError(
            "zero output was verified, but FORTE termination failed"
        ) from terminate_error

    if write_errors:
        print(
            "ZERO-WRITE FALLBACK WARNING: "
            + "; ".join(write_errors)
        )
        print(
            "FINAL ZERO OUTPUT VERIFIED DESPITE WRITE WARNING: YES"
        )

    return final


def print_plan(args: argparse.Namespace) -> int:
    print("HIGH-RANGE MPC V4 REAL-PLANT VALIDATION PLAN")
    print("===========================================")
    print()
    print("THIS STAGE CAN PRODUCE REAL PUMP ACTUATION.")
    print()
    print("Supervisor positive actuator writes: NO")
    print("Supervisor ENABLE_REQUEST writes: NO")
    print("Supervisor safe-zero writes on abort/end: YES")
    print("FORTE automatic termination on abort/end: YES")
    print()
    print(f"Initial raw band: {args.initial_min_raw:.1f} .. {args.initial_max_raw:.1f}")
    print(f"Active window: {args.active_duration_s:.1f} s")
    print(f"Arm timeout: {args.arm_timeout_s:.1f} s")
    print(f"Sample period: {args.sample_s:.3f} s")
    print(f"Maximum DAC: {args.maximum_dac:.1f}")
    print(f"Maximum rolling-median raw: {args.maximum_median_raw:.1f}")
    print(f"Maximum instantaneous raw: {args.maximum_instant_raw:.1f}")
    print(
        "Maximum positive rolling-median rate: "
        f"{args.maximum_rate_raw_per_s:.1f} raw/s"
    )
    print()
    print("Expected 4diac settings before --run:")
    print("  SP_RAW = 16000.0")
    print("  ENABLE_REQUEST = FALSE")
    print("  EXTERNAL_HEALTHY = TRUE")
    print("  controller TRIPPED = FALSE")
    print("  safe limiter DAC_MAX = 16000")
    print("  safe limiter MAX_DELTA_DAC = 750 per 500 ms cycle")
    print()
    print("Run sequence:")
    print("  1. Script verifies initial zero output and healthy watchdog.")
    print("  2. Script prints ARMED.")
    print("  3. Manually change only MpcController.ENABLE_REQUEST to TRUE.")
    print("  4. Script detects real command/output activity and starts the timer.")
    print("  5. Script continuously enforces level/rate/DAC/watchdog limits.")
    print("  6. At active-window end OR any violation, script terminates FORTE.")
    print("  7. Script writes only safe zero values to gateway/PLC and verifies zero.")
    print()
    print("Do not manually change SP_RAW or any controller/model parameter.")
    print("Physical stop must remain immediately accessible.")
    print()
    print(f"Confirmation token for --run: {CONFIRMATION_TOKEN}")
    print()
    print("REAL MPC FULL OPERATION AUTHORIZED: NO")
    return 0


async def execute(args: argparse.Namespace) -> int:
    token = input(
        "Type HIGH_RANGE_MPC_READY only if the physical stop is accessible, "
        "the tank is visually safe, the gateway + canonical MPC FORTE are "
        "running, ResRealRawMPCV4 is deployed and initialized, "
        "ENABLE_REQUEST is FALSE, SP_RAW is 16000, and the bounded limits "
        "printed by --plan are accepted: "
    ).strip()

    if token != CONFIRMATION_TOKEN:
        raise RuntimeError("high-range MPC V4 validation was not confirmed")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_root / f"mpc-v4-high-range-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=False)
    csv_path = output_dir / "first-active-monitor.csv"

    gateway_client = Client(url=args.gateway_endpoint)
    plc_client = Client(url=args.plc_endpoint)

    active_started: float | None = None
    run_started = time.monotonic()
    arm_deadline = run_started + args.arm_timeout_s
    levels: deque[float] = deque(maxlen=9)
    median_history: deque[tuple[float, float]] = deque(maxlen=20)
    samples = 0
    max_seen_dac = 0.0
    max_seen_level = -math.inf
    max_seen_median = -math.inf
    max_seen_rate = 0.0
    shutdown_done = False
    shutdown_reason = ""

    fieldnames = [
        "elapsed_s",
        "active_elapsed_s",
        "gw_nivel",
        "median9_raw",
        "positive_median_rate_raw_per_s",
        "gw_enable",
        "gw_dac",
        "gw_applied_enable",
        "gw_applied_dac",
        "gw_watchdog_healthy",
        "plc_nivel",
        "plc_enable",
        "plc_dac",
        "plc_applied_enable",
        "plc_applied_dac",
        "plc_watchdog_healthy",
        "plc_watchdog_tripped",
    ]

    try:
        await gateway_client.connect()
        await plc_client.connect()

        gateway = await resolve_gateway_nodes(
            gateway_client,
            args.gateway_uri,
        )
        plc = await resolve_plc_nodes(plc_client)

        # Establish a deterministic initial rolling median before arming.
        for _ in range(9):
            initial_sample = await read_snapshot(gateway, plc)
            assert_initial_safe(
                initial_sample,
                args.initial_min_raw,
                args.initial_max_raw,
            )
            levels.append(float(initial_sample["gw_nivel"]))
            await asyncio.sleep(args.sample_s)

        initial_median = statistics.median(levels)

        print()
        print("INITIAL ACTIVE-COMMISSIONING PRECONDITION: PASSED")
        print(f"Initial median9 raw: {initial_median:.1f}")
        print()
        print("ARMED")
        print("Manually set ONLY MpcController.ENABLE_REQUEST = TRUE now.")
        print("Do not change SP_RAW or any other parameter.")
        print(
            f"The supervisor will automatically stop after "
            f"{args.active_duration_s:.1f} active seconds."
        )
        print()

        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                delimiter=";",
            )
            writer.writeheader()

            next_console = time.monotonic()

            while True:
                now = time.monotonic()
                elapsed = now - run_started

                snapshot = await read_snapshot(gateway, plc)
                levels.append(float(snapshot["gw_nivel"]))
                median_raw = statistics.median(levels)

                median_history.append((now, median_raw))

                positive_rate = 0.0
                if len(median_history) >= 2:
                    old_t, old_median = median_history[0]
                    dt = now - old_t
                    if dt > 0:
                        positive_rate = max(
                            0.0,
                            (median_raw - old_median) / dt,
                        )

                activity = (
                    snapshot["gw_enable"] is True
                    or snapshot["gw_applied_enable"] is True
                    or snapshot["gw_dac"] > 1e-9
                    or snapshot["gw_applied_dac"] > 1e-9
                )

                if active_started is None:
                    # Before user authorization, zero output remains mandatory.
                    if activity:
                        active_started = now
                        print()
                        print("ACTIVE MPC OUTPUT DETECTED")
                        print("==========================")
                        print(
                            f"t={elapsed:.3f}s | "
                            f"Enable={snapshot['gw_enable']} | "
                            f"DAC={snapshot['gw_dac']:.1f} | "
                            f"AppliedEnable={snapshot['gw_applied_enable']} | "
                            f"AppliedDAC={snapshot['gw_applied_dac']:.1f}"
                        )
                    elif now >= arm_deadline:
                        shutdown_reason = "ARM_TIMEOUT_WITHOUT_ACTUATION"
                        break

                    # Watchdog health is mandatory even while armed/waiting.
                    if snapshot["gw_watchdog_healthy"] is not True:
                        raise RuntimeError(
                            "gateway WatchdogHealthy became FALSE while armed"
                        )
                    if snapshot["plc_watchdog_healthy"] is not True:
                        raise RuntimeError(
                            "PLC WatchdogHealthy became FALSE while armed"
                        )
                    if snapshot["plc_watchdog_tripped"] is not False:
                        raise RuntimeError(
                            "PLC WatchdogTripped became TRUE while armed"
                        )

                if active_started is not None:
                    active_elapsed = now - active_started

                    assert_active_limits(
                        snapshot,
                        median_raw,
                        positive_rate,
                        maximum_median_raw=args.maximum_median_raw,
                        maximum_instant_raw=args.maximum_instant_raw,
                        maximum_rate_raw_per_s=args.maximum_rate_raw_per_s,
                        maximum_dac=args.maximum_dac,
                    )

                    if (
                        snapshot["gw_enable"] is False
                        and snapshot["gw_applied_enable"] is False
                        and is_zero(snapshot["gw_dac"])
                        and is_zero(snapshot["gw_applied_dac"])
                    ):
                        raise RuntimeError(
                            "controller returned to complete zero output "
                            "before the bounded active window completed"
                        )

                    if active_elapsed >= args.active_duration_s:
                        shutdown_reason = "ACTIVE_WINDOW_COMPLETE"
                        break
                else:
                    active_elapsed = -1.0

                max_seen_dac = max(
                    max_seen_dac,
                    float(snapshot["gw_dac"]),
                    float(snapshot["gw_applied_dac"]),
                    float(snapshot["plc_dac"]),
                    float(snapshot["plc_applied_dac"]),
                )
                max_seen_level = max(
                    max_seen_level,
                    float(snapshot["gw_nivel"]),
                )
                max_seen_median = max(max_seen_median, median_raw)
                max_seen_rate = max(max_seen_rate, positive_rate)
                samples += 1

                writer.writerow(
                    {
                        "elapsed_s": f"{elapsed:.6f}",
                        "active_elapsed_s": f"{active_elapsed:.6f}",
                        "gw_nivel": snapshot["gw_nivel"],
                        "median9_raw": f"{median_raw:.6f}",
                        "positive_median_rate_raw_per_s": f"{positive_rate:.6f}",
                        "gw_enable": snapshot["gw_enable"],
                        "gw_dac": snapshot["gw_dac"],
                        "gw_applied_enable": snapshot["gw_applied_enable"],
                        "gw_applied_dac": snapshot["gw_applied_dac"],
                        "gw_watchdog_healthy": snapshot["gw_watchdog_healthy"],
                        "plc_nivel": snapshot["plc_nivel"],
                        "plc_enable": snapshot["plc_enable"],
                        "plc_dac": snapshot["plc_dac"],
                        "plc_applied_enable": snapshot["plc_applied_enable"],
                        "plc_applied_dac": snapshot["plc_applied_dac"],
                        "plc_watchdog_healthy": snapshot["plc_watchdog_healthy"],
                        "plc_watchdog_tripped": snapshot["plc_watchdog_tripped"],
                    }
                )

                if now >= next_console:
                    active_text = (
                        "ARMED"
                        if active_started is None
                        else f"ACTIVE {active_elapsed:5.1f}s"
                    )
                    print(
                        f"{active_text:12s} | "
                        f"Nivel={snapshot['gw_nivel']:7.1f} | "
                        f"Med9={median_raw:7.1f} | "
                        f"Rate+={positive_rate:6.1f} | "
                        f"Enable={snapshot['gw_enable']} | "
                        f"DAC={snapshot['gw_dac']:7.1f} | "
                        f"AppliedDAC={snapshot['gw_applied_dac']:7.1f} | "
                        f"Healthy={snapshot['gw_watchdog_healthy']}"
                    )
                    next_console = now + 0.5

                await asyncio.sleep(args.sample_s)

        await safe_shutdown(
            forte_pid=args.forte_pid,
            gateway=gateway,
            plc=plc,
            zero_timeout_s=args.zero_timeout_s,
            reason=shutdown_reason,
        )
        shutdown_done = True

        print()
        print("HIGH-RANGE MPC V4 VALIDATION COMPLETED")
        print("===============================================")
        print(f"Shutdown reason: {shutdown_reason}")
        print(f"Samples logged: {samples}")
        print(f"Maximum observed DAC: {max_seen_dac:.1f}")
        print(f"Maximum raw level: {max_seen_level:.1f}")
        print(f"Maximum median9 raw: {max_seen_median:.1f}")
        print(
            "Maximum positive median rate: "
            f"{max_seen_rate:.1f} raw/s"
        )
        print(f"CSV: {csv_path}")
        print()
        if shutdown_reason == "ACTIVE_WINDOW_COMPLETE":
            print("M5F HIGH-RANGE ACTIVE WINDOW: COMPLETED")
        else:
            print("M5F HIGH-RANGE ACTIVE WINDOW: NO ACTUATION OBSERVED")
        print("FINAL ZERO OUTPUT VERIFIED: YES")
        print("FORTE STOPPED AT END: YES")
        print("REAL MPC FULL OPERATION AUTHORIZED: NO")
        print("NEXT: preserve and analyze the complete 15 cm trajectory")
        return 0

    except BaseException as exc:
        print()
        print("M5F HIGH-RANGE ABORT")
        print("=========")
        print(f"Reason: {exc}")

        if "gateway" in locals() and "plc" in locals():
            try:
                await safe_shutdown(
                    forte_pid=args.forte_pid,
                    gateway=gateway,
                    plc=plc,
                    zero_timeout_s=args.zero_timeout_s,
                    reason=f"ABORT: {exc}",
                )
                shutdown_done = True
            except Exception as shutdown_exc:
                print()
                print("AUTOMATIC SAFE SHUTDOWN FAILED")
                print("================================")
                print(str(shutdown_exc))
                print("USE THE PHYSICAL STOP IMMEDIATELY.")

        raise

    finally:
        try:
            await gateway_client.disconnect()
        except Exception:
            pass
        try:
            await plc_client.disconnect()
        except Exception:
            pass

        if not shutdown_done and active_started is not None:
            print()
            print(
                "WARNING: active output may have occurred without a verified "
                "software shutdown. Confirm physical zero state immediately."
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Independent supervisor for the high-range MPC V4 validation. "
            "It never writes positive actuator commands."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")

    parser.add_argument(
        "--forte-pid",
        type=int,
        default=0,
        help="PID of the canonical MPC FORTE; required by --run",
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
        "--plc-endpoint",
        default=DEFAULT_PLC_ENDPOINT,
    )
    parser.add_argument(
        "--initial-min-raw",
        type=float,
        default=240.0,
    )
    parser.add_argument(
        "--initial-max-raw",
        type=float,
        default=340.0,
    )
    parser.add_argument(
        "--active-duration-s",
        type=float,
        default=180.0,
    )
    parser.add_argument(
        "--arm-timeout-s",
        type=float,
        default=60.0,
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--maximum-dac",
        type=float,
        default=16000.0,
    )
    parser.add_argument(
        "--maximum-median-raw",
        type=float,
        default=19000.0,
    )
    parser.add_argument(
        "--maximum-instant-raw",
        type=float,
        default=20000.0,
    )
    parser.add_argument(
        "--maximum-rate-raw-per-s",
        type=float,
        default=500.0,
    )
    parser.add_argument(
        "--zero-timeout-s",
        type=float,
        default=30.0,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.run and args.forte_pid <= 0:
        raise SystemExit("--forte-pid is required and must be positive for --run")

    if args.initial_min_raw >= args.initial_max_raw:
        raise SystemExit("initial raw band is invalid")
    if args.active_duration_s <= 0:
        raise SystemExit("active duration must be positive")
    if args.active_duration_s > 240.0:
        raise SystemExit("high-range duration must not exceed 240 s")
    if args.arm_timeout_s <= 0:
        raise SystemExit("arm timeout must be positive")
    if args.sample_s <= 0:
        raise SystemExit("sample period must be positive")
    if args.maximum_dac <= 0 or args.maximum_dac > 16000:
        raise SystemExit("maximum DAC must be in 1..16000")
    if args.maximum_median_raw <= args.initial_max_raw:
        raise SystemExit("maximum median raw must exceed initial band")
    if args.maximum_instant_raw <= args.maximum_median_raw:
        raise SystemExit("instant raw ceiling must exceed median ceiling")
    if args.maximum_rate_raw_per_s <= 0:
        raise SystemExit("maximum level rate must be positive")
    if args.zero_timeout_s <= 0:
        raise SystemExit("zero timeout must be positive")


def main() -> int:
    args = build_parser().parse_args()
    validate_args(args)

    if args.plan:
        return print_plan(args)

    return asyncio.run(execute(args))


if __name__ == "__main__":
    raise SystemExit(main())