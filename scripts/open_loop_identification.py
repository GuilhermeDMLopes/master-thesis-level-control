from __future__ import annotations

import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path

from asyncua import Client, ua


PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"
GATEWAY_ENDPOINT = "opc.tcp://127.0.0.1:4841"
GATEWAY_URI = "urn:br-4diac-gateway"

TARGET_DAC = 12000
BASELINE_S = 8.0
HOLD_S = 20.0
RECOVERY_S = 10.0
SAMPLE_S = 0.10

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


async def write_only(node, value, variant_type):
    await node.write_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(value, variant_type)
        ),
    )


async def read_plc(client):
    return {
        name: await client.get_node(node_id).read_value()
        for name, node_id in PLC_IDS.items()
    }


def watchdog_ok(state):
    return (
        state["SafetyReset"] is False
        and state["WatchdogHealthy"] is True
        and state["WatchdogTripped"] is False
    )


async def main():
    confirmation = input(
        "Digite IDENTIFICATION_READY com a parada fisica "
        "liberada e pronta para ser acionada: "
    ).strip()

    if confirmation != "IDENTIFICATION_READY":
        raise RuntimeError("Ensaio nao confirmado.")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = (
        Path("data/raw")
        / f"open-loop-identification-{run_id}"
    )
    run_root.mkdir(parents=True, exist_ok=True)

    csv_path = run_root / "open-loop-identification.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "level_raw",
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

            async def sample(phase, writer):
                nonlocal last_print

                state = await read_plc(plc)
                gateway_enable = await enable_node.read_value()
                gateway_dac = await dac_node.read_value()

                writer.writerow(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "elapsed_s": round(
                            time.monotonic() - start,
                            6,
                        ),
                        "phase": phase,
                        "level_raw": int(state["Nivel"]),
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
                        "enable_plc": bool(state["Enable"]),
                        "dac_plc": int(state["DAC"]),
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

                now = time.monotonic()

                if now - last_print >= 0.5:
                    print(
                        f"{phase:12s} | "
                        f"t={now-start:6.2f}s | "
                        f"Nivel={int(state['Nivel']):5d} | "
                        f"Healthy={state['WatchdogHealthy']} | "
                        f"Tripped={state['WatchdogTripped']} | "
                        f"Enable={state['Enable']} | "
                        f"DAC={int(state['DAC']):5d} | "
                        f"AppliedDAC={int(state['AppliedDAC']):5d}"
                    )
                    last_print = now

                return state

            async def record_for(
                phase,
                duration_s,
                writer,
                require_watchdog=True,
            ):
                deadline = time.monotonic() + duration_s

                while time.monotonic() < deadline:
                    state = await sample(phase, writer)

                    if require_watchdog and not watchdog_ok(state):
                        raise RuntimeError(
                            f"Watchdog invalido durante {phase}."
                        )

                    await asyncio.sleep(SAMPLE_S)

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
                    print("Aguardando estado inicial estavel...")

                    stable = 0
                    deadline = time.monotonic() + 12.0

                    while time.monotonic() < deadline:
                        state = await sample(
                            "STARTUP",
                            writer,
                        )

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
                            "Estado inicial nao estabilizou."
                        )

                    print("Registrando baseline...")
                    await record_for(
                        "BASELINE",
                        BASELINE_S,
                        writer,
                    )

                    print("Ativando Enable com DAC=0...")
                    await write_only(
                        enable_node,
                        True,
                        ua.VariantType.Boolean,
                    )

                    deadline = time.monotonic() + 5.0

                    while time.monotonic() < deadline:
                        state = await sample(
                            "ENABLE_ON",
                            writer,
                        )

                        if (
                            watchdog_ok(state)
                            and state["AppliedEnable"] is True
                            and int(state["AppliedDAC"]) == 0
                        ):
                            break

                        await asyncio.sleep(SAMPLE_S)
                    else:
                        raise RuntimeError(
                            "Enable nao foi aplicado."
                        )

                    print("Solicitando DAC=12000...")
                    await write_only(
                        dac_node,
                        TARGET_DAC,
                        ua.VariantType.Int16,
                    )

                    deadline = time.monotonic() + 20.0

                    while time.monotonic() < deadline:
                        state = await sample(
                            "RAMP_UP",
                            writer,
                        )

                        if not watchdog_ok(state):
                            raise RuntimeError(
                                "Watchdog falhou na rampa."
                            )

                        if (
                            int(state["AppliedDAC"])
                            == TARGET_DAC
                        ):
                            break

                        await asyncio.sleep(SAMPLE_S)
                    else:
                        raise RuntimeError(
                            "DAC 12000 nao foi atingido."
                        )

                    print(
                        "DAC 12000 atingido. "
                        "Mantendo por 20 segundos..."
                    )

                    await record_for(
                        "HOLD_12000",
                        HOLD_S,
                        writer,
                    )

                    print(
                        "Desligando imediatamente por Enable=False..."
                    )

                    shutdown_start = time.monotonic()

                    await write_only(
                        enable_node,
                        False,
                        ua.VariantType.Boolean,
                    )

                    deadline = time.monotonic() + 3.0

                    while time.monotonic() < deadline:
                        state = await sample(
                            "ENABLE_OFF",
                            writer,
                        )

                        if (
                            state["AppliedEnable"] is False
                            and int(state["AppliedDAC"]) == 0
                        ):
                            break

                        await asyncio.sleep(SAMPLE_S)
                    else:
                        raise RuntimeError(
                            "Saida aplicada nao foi removida."
                        )

                    print(
                        "Saida removida em "
                        f"{time.monotonic()-shutdown_start:.3f} s"
                    )

                    await write_only(
                        dac_node,
                        0,
                        ua.VariantType.Int16,
                    )

                    print("Registrando recuperacao...")
                    await record_for(
                        "RECOVERY",
                        RECOVERY_S,
                        writer,
                    )

                    print()
                    print(
                        "Open-loop identification sequence: PASSED"
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
                        print("Final safe commands written.")
                    except Exception as error:
                        print(f"Cleanup warning: {error!r}")


asyncio.run(main())
