from __future__ import annotations

import argparse
import asyncio
import csv
import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from asyncua import Client, ua


DEFAULT_GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
DEFAULT_GATEWAY_URI = "urn:br-4diac-gateway"
DEFAULT_PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
DEFAULT_OUTPUT_ROOT = Path("data/raw")


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
    enable: object
    dac: object
    applied_enable: object | None
    applied_dac: object | None
    watchdog_healthy: object | None


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


def exact_zero(value: object) -> bool:
    return abs(finite_number(value)) <= 1e-9


async def read_value(node: object) -> object:
    return await node.read_value()


async def resolve_gateway_nodes(
    client: Client,
    namespace_uri: str,
) -> GatewayNodes:
    namespace_index = await client.get_namespace_index(namespace_uri)

    def node(name: str):
        return client.get_node(
            ua.NodeId(name, namespace_index, ua.NodeIdType.String)
        )

    resolved = GatewayNodes(
        nivel=node("Nivel"),
        enable=node("Enable"),
        dac=node("DAC"),
        applied_enable=node("AppliedEnable"),
        applied_dac=node("AppliedDAC"),
        watchdog_healthy=node("WatchdogHealthy"),
    )

    # Fail early if the expected runtime contract is not exposed.
    for label, target in (
        ("Nivel", resolved.nivel),
        ("Enable", resolved.enable),
        ("DAC", resolved.dac),
        ("AppliedEnable", resolved.applied_enable),
        ("AppliedDAC", resolved.applied_dac),
        ("WatchdogHealthy", resolved.watchdog_healthy),
    ):
        try:
            await target.read_value()
        except Exception as exc:
            raise RuntimeError(
                f"gateway node {label!r} is not readable"
            ) from exc

    return resolved


async def optional_plc_node(
    client: Client,
    candidates: list[str],
):
    for identifier in candidates:
        target = client.get_node(identifier)
        try:
            await target.read_value()
        except Exception:
            continue
        return target
    return None


async def resolve_plc_nodes(client: Client) -> PlcNodes:
    # The first two logical names are part of the established B&R contract.
    enable = client.get_node("ns=6;s=::AsGlobalPV:Program:Enable")
    dac = client.get_node("ns=6;s=::AsGlobalPV:Program:DAC")

    # B&R namespace indices can differ between builds. Fall back to browse-like
    # candidate NodeIds for optional feedback signals; failure here does not
    # weaken the mandatory gateway checks below.
    try:
        await enable.read_value()
        await dac.read_value()
    except Exception:
        # Generic string NodeIds used by some B&R OPC UA configurations.
        enable = await optional_plc_node(
            client,
            [
                "ns=6;s=Program:Enable",
                "ns=5;s=Program:Enable",
                "ns=4;s=Program:Enable",
                "ns=3;s=Program:Enable",
            ],
        )
        dac = await optional_plc_node(
            client,
            [
                "ns=6;s=Program:DAC",
                "ns=5;s=Program:DAC",
                "ns=4;s=Program:DAC",
                "ns=3;s=Program:DAC",
            ],
        )

        if enable is None or dac is None:
            raise RuntimeError(
                "could not resolve mandatory PLC Enable/DAC readback nodes"
            )

    applied_enable = await optional_plc_node(
        client,
        [
            "ns=6;s=::AsGlobalPV:Program:AppliedEnable",
            "ns=6;s=Program:AppliedEnable",
            "ns=5;s=Program:AppliedEnable",
            "ns=4;s=Program:AppliedEnable",
        ],
    )
    applied_dac = await optional_plc_node(
        client,
        [
            "ns=6;s=::AsGlobalPV:Program:AppliedDAC",
            "ns=6;s=Program:AppliedDAC",
            "ns=5;s=Program:AppliedDAC",
            "ns=4;s=Program:AppliedDAC",
        ],
    )
    watchdog_healthy = await optional_plc_node(
        client,
        [
            "ns=6;s=::AsGlobalPV:Program:WatchdogHealthy",
            "ns=6;s=Program:WatchdogHealthy",
            "ns=5;s=Program:WatchdogHealthy",
            "ns=4;s=Program:WatchdogHealthy",
        ],
    )

    return PlcNodes(
        enable=enable,
        dac=dac,
        applied_enable=applied_enable,
        applied_dac=applied_dac,
        watchdog_healthy=watchdog_healthy,
    )


async def read_gateway_snapshot(nodes: GatewayNodes) -> dict[str, object]:
    values = await asyncio.gather(
        read_value(nodes.nivel),
        read_value(nodes.enable),
        read_value(nodes.dac),
        read_value(nodes.applied_enable),
        read_value(nodes.applied_dac),
        read_value(nodes.watchdog_healthy),
    )

    return {
        "gw_nivel": finite_number(values[0]),
        "gw_enable": bool_value(values[1]),
        "gw_dac": finite_number(values[2]),
        "gw_applied_enable": bool_value(values[3]),
        "gw_applied_dac": finite_number(values[4]),
        "gw_watchdog_healthy": bool_value(values[5]),
    }


async def read_plc_snapshot(nodes: PlcNodes) -> dict[str, object]:
    result: dict[str, object] = {
        "plc_enable": bool_value(await read_value(nodes.enable)),
        "plc_dac": finite_number(await read_value(nodes.dac)),
        "plc_applied_enable": "",
        "plc_applied_dac": "",
        "plc_watchdog_healthy": "",
    }

    if nodes.applied_enable is not None:
        result["plc_applied_enable"] = bool_value(
            await read_value(nodes.applied_enable)
        )
    if nodes.applied_dac is not None:
        result["plc_applied_dac"] = finite_number(
            await read_value(nodes.applied_dac)
        )
    if nodes.watchdog_healthy is not None:
        result["plc_watchdog_healthy"] = bool_value(
            await read_value(nodes.watchdog_healthy)
        )

    return result


def assert_zero_output(snapshot: dict[str, object]) -> None:
    failures: list[str] = []

    if snapshot["gw_enable"] is not False:
        failures.append(f"gateway Enable={snapshot['gw_enable']!r}")
    if not exact_zero(snapshot["gw_dac"]):
        failures.append(f"gateway DAC={snapshot['gw_dac']!r}")
    if snapshot["gw_applied_enable"] is not False:
        failures.append(
            f"gateway AppliedEnable={snapshot['gw_applied_enable']!r}"
        )
    if not exact_zero(snapshot["gw_applied_dac"]):
        failures.append(
            f"gateway AppliedDAC={snapshot['gw_applied_dac']!r}"
        )

    if snapshot["plc_enable"] is not False:
        failures.append(f"PLC Enable={snapshot['plc_enable']!r}")
    if not exact_zero(snapshot["plc_dac"]):
        failures.append(f"PLC DAC={snapshot['plc_dac']!r}")

    if snapshot["plc_applied_enable"] != "":
        if snapshot["plc_applied_enable"] is not False:
            failures.append(
                f"PLC AppliedEnable={snapshot['plc_applied_enable']!r}"
            )

    if snapshot["plc_applied_dac"] != "":
        if not exact_zero(snapshot["plc_applied_dac"]):
            failures.append(
                f"PLC AppliedDAC={snapshot['plc_applied_dac']!r}"
            )

    if failures:
        raise RuntimeError(
            "ZERO-OUTPUT VIOLATION: " + "; ".join(failures)
        )


def print_plan(args: argparse.Namespace) -> int:
    print("MPC ZERO-OUTPUT DEPLOYMENT GUARD PLAN")
    print("=====================================")
    print("NETWORK ACCESS: NO")
    print("OPC UA WRITES: NO")
    print("FORTE DEPLOYMENT AUTOMATION: NO")
    print("ACTUATOR COMMANDS: NO")
    print()
    print(f"Gateway endpoint: {args.gateway_endpoint}")
    print(f"Gateway URI: {args.gateway_uri}")
    print(f"PLC endpoint: {args.plc_endpoint}")
    print(f"Observation duration: {args.duration_s:.1f} s")
    print(f"Sampling period: {args.sample_s:.3f} s")
    print()
    print("During --observe the script only READS PLC/gateway state.")
    print("It aborts immediately if Enable/AppliedEnable becomes TRUE")
    print("or DAC/AppliedDAC becomes non-zero.")
    print()
    print("While it is running, manually deploy ResRealRawMPCV1 in 4diac.")
    print("Do not change MpcController.ENABLE_REQUEST from FALSE.")
    print("After deployment, manually trigger MpcInitMerge.EI1 once.")
    print("Do not trigger or edit any other control input.")
    print()
    print("Confirmation token: MPC_ZERO_OUTPUT_GUARD_READY")
    return 0


async def observe(args: argparse.Namespace) -> int:
    token = input(
        "Type MPC_ZERO_OUTPUT_GUARD_READY only if physical stop is "
        "accessible, PI/MPC actuation is disabled, gateway + FORTE are "
        "running, and MpcController.ENABLE_REQUEST is FALSE: "
    ).strip()

    if token != "MPC_ZERO_OUTPUT_GUARD_READY":
        raise RuntimeError("zero-output deployment guard was not confirmed")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_root / f"mpc-zero-output-deploy-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=False)
    csv_path = output_dir / "zero-output-monitor.csv"

    print()
    print("Connecting read-only guard...")
    print(f"  gateway: {args.gateway_endpoint}")
    print(f"  PLC:     {args.plc_endpoint}")

    gateway = Client(url=args.gateway_endpoint)
    plc = Client(url=args.plc_endpoint)

    levels: list[float] = []
    healthy_seen = False
    samples = 0
    started = asyncio.get_running_loop().time()
    next_console = started

    fieldnames = [
        "elapsed_s",
        "gw_nivel",
        "gw_enable",
        "gw_dac",
        "gw_applied_enable",
        "gw_applied_dac",
        "gw_watchdog_healthy",
        "plc_enable",
        "plc_dac",
        "plc_applied_enable",
        "plc_applied_dac",
        "plc_watchdog_healthy",
    ]

    try:
        await gateway.connect()
        await plc.connect()

        gateway_nodes = await resolve_gateway_nodes(
            gateway,
            args.gateway_uri,
        )
        plc_nodes = await resolve_plc_nodes(plc)

        initial = {
            **await read_gateway_snapshot(gateway_nodes),
            **await read_plc_snapshot(plc_nodes),
        }
        assert_zero_output(initial)

        print()
        print("INITIAL ZERO OUTPUT: PASSED")
        print(
            "Now deploy ONLY ResRealRawMPCV1 in Eclipse 4diac, keep "
            "ENABLE_REQUEST=FALSE, then manually trigger MpcInitMerge.EI1 once."
        )
        print(
            "This guard will continue monitoring and will abort on any "
            "non-zero actuator state."
        )
        print()

        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                delimiter=";",
            )
            writer.writeheader()

            while True:
                now = asyncio.get_running_loop().time()
                elapsed = now - started

                if elapsed >= args.duration_s:
                    break

                snapshot = {
                    **await read_gateway_snapshot(gateway_nodes),
                    **await read_plc_snapshot(plc_nodes),
                }

                assert_zero_output(snapshot)

                levels.append(float(snapshot["gw_nivel"]))
                healthy_seen = (
                    healthy_seen
                    or bool(snapshot["gw_watchdog_healthy"])
                )
                samples += 1

                writer.writerow(
                    {
                        "elapsed_s": f"{elapsed:.6f}",
                        **snapshot,
                    }
                )

                if now >= next_console:
                    print(
                        f"t={elapsed:6.1f}s | "
                        f"Nivel={snapshot['gw_nivel']:7.1f} | "
                        f"Enable={snapshot['gw_enable']} | "
                        f"DAC={snapshot['gw_dac']:7.1f} | "
                        f"AppliedEnable={snapshot['gw_applied_enable']} | "
                        f"AppliedDAC={snapshot['gw_applied_dac']:7.1f} | "
                        f"Healthy={snapshot['gw_watchdog_healthy']}"
                    )
                    next_console = now + 1.0

                await asyncio.sleep(args.sample_s)

        final = {
            **await read_gateway_snapshot(gateway_nodes),
            **await read_plc_snapshot(plc_nodes),
        }
        assert_zero_output(final)

    finally:
        try:
            await gateway.disconnect()
        except Exception:
            pass
        try:
            await plc.disconnect()
        except Exception:
            pass

    if not levels:
        raise RuntimeError("no valid samples were recorded")

    print()
    print("MPC ZERO-OUTPUT DEPLOYMENT GUARD COMPLETED")
    print("==========================================")
    print(f"Samples: {samples}")
    print(
        "Nivel raw range: "
        f"{min(levels):.1f} .. {max(levels):.1f}"
    )
    print(f"Nivel raw median: {statistics.median(levels):.3f}")
    print(f"WatchdogHealthy observed TRUE: {healthy_seen}")
    print("FINAL Enable=False: YES")
    print("FINAL DAC=0: YES")
    print("FINAL AppliedEnable=False: YES")
    print("FINAL AppliedDAC=0: YES")
    print("OPC UA WRITES BY GUARD: NO")
    print(f"CSV: {csv_path}")
    print()
    print("ZERO-OUTPUT DEPLOYMENT VALIDATION: PASSED")
    print("REAL MPC AUTHORIZED: NO")
    print("NEXT: inspect FORTE/4diac runtime inputs before any MPC enable")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only guard for the first disabled MPC resource deployment. "
            "It never writes OPC UA values and never deploys FORTE."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--observe", action="store_true")

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
        "--duration-s",
        type=float,
        default=90.0,
    )
    parser.add_argument(
        "--sample-s",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.duration_s <= 0:
        raise SystemExit("duration must be positive")
    if args.sample_s <= 0:
        raise SystemExit("sample period must be positive")

    if args.plan:
        return print_plan(args)

    return asyncio.run(observe(args))


if __name__ == "__main__":
    raise SystemExit(main())
