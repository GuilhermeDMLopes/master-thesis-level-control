from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from asyncua import Client, ua


SCRIPT_PATH = Path(__file__).resolve()
REPOSITORY = SCRIPT_PATH.parents[2]

EXPECTED_BRANCH = "feature/real-positive-dac-commissioning"

PROJECT_FILE = (
    REPOSITORY
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
    / "OPAS_Tank_System.sys"
)

GATEWAY_SCRIPT = REPOSITORY / "gateway" / "src" / "gateway_opcua.py"

FORTE_EXE = Path(
    r"C:\Projetos\forte-offline-safe-dac-validation\forte.exe"
)

FORTE_SHA256 = (
    "3D0C115C256844ACC243CF46E29109E7E0EFA0F52DC6D2ED2D734FED08430FE3"
)

PLC_ENDPOINT = "opc.tcp://10.0.0.3:4840"

PLC_NODES = {
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

STATE_FILE = (
    Path(tempfile.gettempdir())
    / "pi_tuned_test_stack_state.json"
)

SAMPLE_S = 0.15


def heading(title: str) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def wait_port(
    host: str,
    port: int,
    expected_open: bool,
    timeout_s: float,
) -> None:
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        if port_open(host, port) is expected_open:
            return

        time.sleep(0.2)

    state = "open" if expected_open else "closed"
    raise RuntimeError(
        f"Port {host}:{port} did not become {state}."
    )


def number_value(value: str | None) -> float:
    if value is None:
        raise RuntimeError("Missing numeric parameter value.")

    text = value.strip()

    if "#" in text:
        text = text.split("#", 1)[1]

    return float(text)


def boolean_value(value: str | None) -> bool:
    if value is None:
        raise RuntimeError("Missing Boolean parameter value.")

    return value.strip().upper() == "TRUE"


def find_named_element(
    root: ET.Element,
    tag: str,
    name: str,
) -> ET.Element:
    matches = [
        item
        for item in root.iter(tag)
        if item.get("Name") == name
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {tag} named {name}; "
            f"found {len(matches)}."
        )

    return matches[0]


def parameters(element: ET.Element) -> dict[str, str]:
    return {
        item.get("Name", ""): item.get("Value", "")
        for item in element.findall("Parameter")
    }


def assert_close(
    actual: float,
    expected: float,
    name: str,
    tolerance: float = 1e-9,
) -> None:
    if abs(actual - expected) > tolerance:
        raise RuntimeError(
            f"{name}={actual}; expected {expected}."
        )


def validate_project_configuration() -> None:
    if not PROJECT_FILE.is_file():
        raise RuntimeError(
            f"4diac project file not found: {PROJECT_FILE}"
        )

    root = ET.parse(PROJECT_FILE).getroot()

    application = find_named_element(
        root,
        "Application",
        "PI_REAL_RAW_SAFE",
    )

    device = find_named_element(
        root,
        "Device",
        "FORTE_PC",
    )

    resources = [
        item
        for item in device.findall("Resource")
        if item.get("Name") == "ResRealRawPI"
    ]

    if len(resources) != 1:
        raise RuntimeError(
            "ResRealRawPI must exist exactly once."
        )

    raw_pi = find_named_element(
        application,
        "FB",
        "RawPI",
    )
    raw_filter = find_named_element(
        application,
        "FB",
        "RawPVFilter",
    )
    limiter = find_named_element(
        application,
        "FB",
        "RawSafeDACLimiter",
    )
    bias = find_named_element(
        application,
        "FB",
        "RawDACBias",
    )

    pi = parameters(raw_pi)
    pv_filter = parameters(raw_filter)
    safe_limiter = parameters(limiter)
    dac_bias = parameters(bias)

    assert_close(
        number_value(pi.get("SETPOINT")),
        450.0,
        "RawPI.SETPOINT",
    )
    assert_close(
        number_value(pi.get("PROPORTIONAL_GAIN")),
        4.0,
        "RawPI.PROPORTIONAL_GAIN",
    )
    assert_close(
        number_value(pi.get("INTEGRAL_GAIN")),
        0.02,
        "RawPI.INTEGRAL_GAIN",
    )
    assert_close(
        number_value(pi.get("SAMPLING_TIME_S")),
        0.1,
        "RawPI.SAMPLING_TIME_S",
    )
    assert_close(
        number_value(pi.get("OUTPUT_MIN")),
        -9000.0,
        "RawPI.OUTPUT_MIN",
    )
    assert_close(
        number_value(pi.get("OUTPUT_MAX")),
        3000.0,
        "RawPI.OUTPUT_MAX",
    )

    if boolean_value(pi.get("MANUAL")) is not True:
        raise RuntimeError("RawPI.MANUAL must be TRUE.")

    assert_close(
        number_value(pi.get("MANUAL_OUTPUT")),
        -9000.0,
        "RawPI.MANUAL_OUTPUT",
    )
    assert_close(
        number_value(pv_filter.get("ALPHA")),
        0.98,
        "RawPVFilter.ALPHA",
    )
    assert_close(
        number_value(safe_limiter.get("MAX_DELTA_DAC")),
        150.0,
        "RawSafeDACLimiter.MAX_DELTA_DAC",
    )
    assert_close(
        number_value(safe_limiter.get("DAC_MIN")),
        0.0,
        "RawSafeDACLimiter.DAC_MIN",
    )
    assert_close(
        number_value(safe_limiter.get("DAC_MAX")),
        12000.0,
        "RawSafeDACLimiter.DAC_MAX",
    )
    assert_close(
        number_value(safe_limiter.get("INITIAL_DAC")),
        0.0,
        "RawSafeDACLimiter.INITIAL_DAC",
    )
    assert_close(
        number_value(dac_bias.get("IN2")),
        9000.0,
        "RawDACBias.IN2",
    )

    print("4diac tuned PI configuration: PASSED")
    print("  SP=450")
    print("  KP=4")
    print("  KI=0.02")
    print("  ALPHA=0.98")
    print("  MANUAL=TRUE")
    print("  MANUAL_OUTPUT=-9000")
    print("  physical DAC range=0..12000")


def validate_repository() -> None:
    branch = run_git("branch", "--show-current")
    status = run_git("status", "--short")

    print(f"Repository: {REPOSITORY}")
    print(f"Branch: {branch}")
    print(
        "Working tree clean: "
        f"{not bool(status.strip())}"
    )

    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Unexpected branch: {branch}"
        )

    if status.strip():
        print(status)
        raise RuntimeError(
            "Working tree must be clean."
        )


async def read_plc_state(
    client: Client,
) -> dict[str, Any]:
    return {
        name: await client.get_node(
            node_id
        ).read_value()
        for name, node_id in PLC_NODES.items()
    }


def format_state(
    phase: str,
    state: dict[str, Any],
    reference: float,
) -> str:
    return (
        f"{phase:16s} | "
        f"t={time.monotonic()-reference:6.2f}s | "
        f"Nivel={int(state['Nivel']):5d} | "
        f"HB={int(state['Heartbeat']):7d} | "
        f"Healthy={state['WatchdogHealthy']} | "
        f"Tripped={state['WatchdogTripped']} | "
        f"Enable={state['Enable']} | "
        f"DAC={int(state['DAC']):5d} | "
        f"AppliedEnable={state['AppliedEnable']} | "
        f"AppliedDAC={int(state['AppliedDAC']):5d}"
    )


def validate_active_watchdog(
    state: dict[str, Any],
) -> None:
    if state["SafetyReset"] is not False:
        raise RuntimeError("SafetyReset became active.")

    if state["WatchdogHealthy"] is not True:
        raise RuntimeError("WatchdogHealthy became false.")

    if state["WatchdogTripped"] is not False:
        raise RuntimeError("WatchdogTripped became true.")

    dac = int(state["DAC"])
    applied_dac = int(state["AppliedDAC"])

    if not 0 <= dac <= 12000:
        raise RuntimeError(
            f"PLC DAC outside 0..12000: {dac}"
        )

    if not 0 <= applied_dac <= 12000:
        raise RuntimeError(
            f"AppliedDAC outside 0..12000: {applied_dac}"
        )


async def validate_plc_safe_trip() -> None:
    states: list[dict[str, Any]] = []

    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as client:
        for sample in range(5):
            state = await read_plc_state(client)
            states.append(state)

            print(
                f"safe sample={sample} | "
                f"HB={int(state['Heartbeat'])} | "
                f"Healthy={state['WatchdogHealthy']} | "
                f"Tripped={state['WatchdogTripped']} | "
                f"Enable={state['Enable']} | "
                f"DAC={int(state['DAC'])} | "
                f"AppliedEnable={state['AppliedEnable']} | "
                f"AppliedDAC={int(state['AppliedDAC'])}"
            )

            await asyncio.sleep(0.2)

    final = states[-1]
    heartbeat_values = {
        int(item["Heartbeat"])
        for item in states
    }

    checks = {
        "Heartbeat stopped": len(heartbeat_values) == 1,
        "Enable=False": final["Enable"] is False,
        "DAC=0": int(final["DAC"]) == 0,
        "SafetyReset=False":
            final["SafetyReset"] is False,
        "WatchdogHealthy=False":
            final["WatchdogHealthy"] is False,
        "WatchdogTripped=True":
            final["WatchdogTripped"] is True,
        "AppliedEnable=False":
            final["AppliedEnable"] is False,
        "AppliedDAC=0":
            int(final["AppliedDAC"]) == 0,
    }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    if failed:
        raise RuntimeError(
            "PLC safe-trip validation failed: "
            + ", ".join(failed)
        )

    print("PLC safe-trip state: PASSED")


async def validate_active_zero() -> None:
    heartbeat_values: list[int] = []

    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as client:
        for sample in range(10):
            state = await read_plc_state(client)
            validate_active_watchdog(state)

            if state["Enable"] is not False:
                raise RuntimeError("Enable is not FALSE.")

            if int(state["DAC"]) != 0:
                raise RuntimeError("DAC is not zero.")

            if state["AppliedEnable"] is not False:
                raise RuntimeError(
                    "AppliedEnable is not FALSE."
                )

            if int(state["AppliedDAC"]) != 0:
                raise RuntimeError(
                    "AppliedDAC is not zero."
                )

            heartbeat_values.append(
                int(state["Heartbeat"])
            )

            print(
                f"active-zero sample={sample} | "
                f"HB={int(state['Heartbeat'])} | "
                f"Healthy={state['WatchdogHealthy']} | "
                f"Tripped={state['WatchdogTripped']} | "
                f"Enable={state['Enable']} | "
                f"DAC={int(state['DAC'])} | "
                f"AppliedEnable={state['AppliedEnable']} | "
                f"AppliedDAC={int(state['AppliedDAC'])}"
            )

            await asyncio.sleep(0.2)

    if len(set(heartbeat_values)) < 3:
        raise RuntimeError(
            "Heartbeat did not remain active."
        )

    print("Active zero-output state: PASSED")


def load_state_file() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {}

    return json.loads(
        STATE_FILE.read_text(
            encoding="utf-8"
        )
    )


def save_state_file(data: dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


def process_exists(pid: int) -> bool:
    result = subprocess.run(
        [
            "tasklist",
            "/FI",
            f"PID eq {pid}",
            "/NH",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    return str(pid) in result.stdout


def kill_pid(pid: int) -> None:
    if pid <= 0:
        return

    subprocess.run(
        [
            "taskkill",
            "/PID",
            str(pid),
            "/T",
            "/F",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def stop_related_processes() -> None:
    state = load_state_file()

    gateway_pid = int(
        state.get("gateway_pid", 0)
    )
    forte_pid = int(
        state.get("forte_pid", 0)
    )

    if gateway_pid:
        print(
            f"Stopping gateway PID {gateway_pid}..."
        )
        kill_pid(gateway_pid)

    time.sleep(1.5)

    if forte_pid:
        print(
            f"Stopping FORTE PID {forte_pid}..."
        )
        kill_pid(forte_pid)

    powershell = (
        "$p = Get-CimInstance Win32_Process | "
        "Where-Object { "
        "($_.Name -eq 'forte.exe') -or "
        "($_.Name -match '^pythonw?\\.exe$' -and "
        "$_.CommandLine -match "
        "'gateway_opcua|br_plc_simulator') }; "
        "$p | ForEach-Object { "
        "Stop-Process -Id $_.ProcessId -Force "
        "-ErrorAction SilentlyContinue }"
    )

    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            powershell,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    time.sleep(0.8)

    if STATE_FILE.exists():
        STATE_FILE.unlink()


async def write_safe_plc_commands() -> None:
    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as client:
        enable_node = client.get_node(
            PLC_NODES["Enable"]
        )
        dac_node = client.get_node(
            PLC_NODES["DAC"]
        )

        await enable_node.write_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(
                    False,
                    ua.VariantType.Boolean,
                )
            ),
        )

        await dac_node.write_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(
                    0,
                    ua.VariantType.Int16,
                )
            ),
        )

    print("Direct safe PLC commands written.")


async def emergency_stop(reason: str) -> None:
    heading("AUTOMATIC EMERGENCY CLEANUP")
    print(reason)
    print("The physical stop must remain active.")

    stop_related_processes()

    try:
        await write_safe_plc_commands()
    except Exception as error:
        print(
            "Direct safe command warning: "
            f"{error!r}"
        )

    await asyncio.sleep(0.8)

    try:
        await validate_plc_safe_trip()
    except Exception as error:
        print(
            "Final safe-trip validation warning: "
            f"{error!r}"
        )


async def command_preflight() -> None:
    heading("ETAPA 6.9F - TUNED PI PREFLIGHT")

    validate_repository()
    validate_project_configuration()

    if not GATEWAY_SCRIPT.is_file():
        raise RuntimeError(
            f"Gateway script not found: {GATEWAY_SCRIPT}"
        )

    if not FORTE_EXE.is_file():
        raise RuntimeError(
            f"FORTE executable not found: {FORTE_EXE}"
        )

    actual_hash = sha256(FORTE_EXE)

    print(f"FORTE SHA256: {actual_hash}")

    if actual_hash != FORTE_SHA256:
        raise RuntimeError(
            "FORTE hash does not match the "
            "validated runtime."
        )

    if port_open("127.0.0.1", 4841):
        raise RuntimeError(
            "Gateway port 4841 is already open."
        )

    if port_open("127.0.0.1", 61499):
        raise RuntimeError(
            "FORTE port 61499 is already open."
        )

    if not port_open("10.0.0.3", 4840):
        raise RuntimeError(
            "PLC OPC UA port 4840 is unavailable."
        )

    await validate_plc_safe_trip()

    print()
    print("PREFLIGHT: PASSED")
    print("READY TO START TUNED PI STACK: YES")
    print("READY FOR AUTOMATIC PI EXECUTION: NO")


async def command_start() -> None:
    confirmation = input(
        "Digite STOP_ACTIVE para confirmar "
        "a parada fisica ativa: "
    ).strip()

    if confirmation != "STOP_ACTIVE":
        raise RuntimeError(
            "Physical stop was not confirmed."
        )

    await command_preflight()

    run_id = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    run_root = (
        REPOSITORY
        / "data"
        / "raw"
        / f"pi-tuned-test-{run_id}"
    )
    run_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    gateway_log = run_root / "gateway.log"
    forte_log = run_root / "forte.log"

    gateway_stream = gateway_log.open(
        "w",
        encoding="utf-8",
        buffering=1,
    )
    forte_stream = forte_log.open(
        "w",
        encoding="utf-8",
        buffering=1,
    )

    environment = os.environ.copy()
    environment["BR_ENDPOINT"] = PLC_ENDPOINT
    environment["PYTHONUNBUFFERED"] = "1"

    creation_flags = getattr(
        subprocess,
        "CREATE_NEW_PROCESS_GROUP",
        0,
    )

    heading("STARTING GATEWAY")

    gateway = subprocess.Popen(
        [
            sys.executable,
            str(GATEWAY_SCRIPT),
        ],
        cwd=REPOSITORY,
        env=environment,
        stdout=gateway_stream,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )

    save_state_file(
        {
            "run_root": str(run_root),
            "gateway_pid": gateway.pid,
            "forte_pid": 0,
        }
    )

    try:
        wait_port(
            "127.0.0.1",
            4841,
            True,
            15.0,
        )

        print(
            f"Gateway PID: {gateway.pid}"
        )
        print("Gateway port 4841: LISTENING")

        heading("STARTING FORTE")

        forte = subprocess.Popen(
            [str(FORTE_EXE)],
            cwd=FORTE_EXE.parent,
            stdout=forte_stream,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )

        save_state_file(
            {
                "run_root": str(run_root),
                "gateway_pid": gateway.pid,
                "forte_pid": forte.pid,
            }
        )

        wait_port(
            "127.0.0.1",
            61499,
            True,
            15.0,
        )

        print(f"FORTE PID: {forte.pid}")
        print("FORTE port 61499: LISTENING")

        heading("ACTIVE ZERO-OUTPUT CHECK")

        await asyncio.sleep(1.0)
        await validate_active_zero()

    except Exception:
        stop_related_processes()
        raise
    finally:
        gateway_stream.close()
        forte_stream.close()

    heading("STACK READY")

    print(f"Run root: {run_root}")
    print(f"Gateway log: {gateway_log}")
    print(f"FORTE log: {forte_log}")
    print()
    print("In 4diac:")
    print("1. Open PI_REAL_RAW_SAFE.")
    print("2. Deploy only PI_REAL_RAW_SAFE.")
    print("3. Enter monitoring.")
    print("4. Trigger RawInitMerge.EI1 once.")
    print("5. Confirm MANUAL=TRUE.")
    print("6. Confirm MANUAL_OUTPUT=-9000.")
    print("7. Confirm RawDACBias.OUT=0.")
    print("8. Confirm RawSafeDACLimiter.DAC_OUT=0.")
    print()
    print("STACK START: PASSED")
    print("READY FOR TUNED PI MONITOR: YES")
    print("READY FOR AUTOMATIC PI EXECUTION: NO")


async def command_monitor() -> None:
    confirmation = input(
        "Digite STOP_ACTIVE para confirmar "
        "a parada fisica ativa no inicio: "
    ).strip()

    if confirmation != "STOP_ACTIVE":
        raise RuntimeError(
            "Physical stop was not confirmed."
        )

    if not port_open("127.0.0.1", 4841):
        raise RuntimeError(
            "Gateway port 4841 is not open."
        )

    if not port_open("127.0.0.1", 61499):
        raise RuntimeError(
            "FORTE port 61499 is not open."
        )

    state_data = load_state_file()
    run_root_text = state_data.get(
        "run_root",
        "",
    )

    if run_root_text:
        run_root = Path(run_root_text)
    else:
        run_id = datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
        run_root = (
            REPOSITORY
            / "data"
            / "raw"
            / f"pi-tuned-test-{run_id}"
        )

    run_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = run_root / "pi-tuned-monitor.csv"

    fields = [
        "timestamp",
        "elapsed_s",
        "phase",
        "level_raw",
        "rolling_median_level",
        "heartbeat",
        "watchdog_healthy",
        "watchdog_tripped",
        "safety_reset",
        "enable",
        "dac",
        "applied_enable",
        "applied_dac",
    ]

    heading("ETAPA 6.9F - TUNED PI TEST")

    print("Physical stop remains active initially.")
    print()
    print("4diac sequence:")
    print("1. Keep RawPI.MANUAL=TRUE.")
    print("2. Set MANUAL_OUTPUT=3000.")
    print("3. Release the physical stop.")
    print("4. At filtered PV 380..400, set MANUAL_OUTPUT=2700.")
    print(
        "5. At filtered PV 420..450, "
        "set MANUAL=FALSE."
    )
    print(
        "6. When requested, set "
        "MANUAL_OUTPUT=-9000, then MANUAL=TRUE."
    )
    print()

    start = time.monotonic()
    last_print = 0.0
    level_window: deque[int] = deque(
        maxlen=9
    )

    async with Client(
        PLC_ENDPOINT,
        timeout=5.0,
    ) as client:
        initial = await read_plc_state(client)
        validate_active_watchdog(initial)

        if not (
            initial["Enable"] is False
            and int(initial["DAC"]) == 0
            and initial["AppliedEnable"] is False
            and int(initial["AppliedDAC"]) == 0
        ):
            raise RuntimeError(
                "Initial zero-output state is invalid."
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

            async def sample(
                phase: str,
                reference: float,
            ) -> tuple[dict[str, Any], float]:
                nonlocal last_print

                state = await read_plc_state(client)
                validate_active_watchdog(state)

                level = int(state["Nivel"])
                level_window.append(level)
                rolling_median = float(
                    statistics.median(level_window)
                )

                if (
                    len(level_window) == level_window.maxlen
                    and rolling_median >= 750.0
                ):
                    raise RuntimeError(
                        "Rolling-median raw level reached "
                        f"{rolling_median:.1f}."
                    )

                elapsed = time.monotonic() - start

                writer.writerow(
                    {
                        "timestamp":
                            datetime.now().isoformat(),
                        "elapsed_s":
                            round(elapsed, 6),
                        "phase": phase,
                        "level_raw": level,
                        "rolling_median_level":
                            round(rolling_median, 3),
                        "heartbeat":
                            int(state["Heartbeat"]),
                        "watchdog_healthy":
                            bool(
                                state[
                                    "WatchdogHealthy"
                                ]
                            ),
                        "watchdog_tripped":
                            bool(
                                state[
                                    "WatchdogTripped"
                                ]
                            ),
                        "safety_reset":
                            bool(state["SafetyReset"]),
                        "enable":
                            bool(state["Enable"]),
                        "dac":
                            int(state["DAC"]),
                        "applied_enable":
                            bool(
                                state[
                                    "AppliedEnable"
                                ]
                            ),
                        "applied_dac":
                            int(state["AppliedDAC"]),
                    }
                )
                stream.flush()

                now = time.monotonic()

                if now - last_print >= 0.5:
                    print(
                        format_state(
                            phase,
                            state,
                            reference,
                        )
                        + " | "
                        + (
                            "Median9="
                            f"{rolling_median:.1f}"
                        )
                    )
                    last_print = now

                return state, rolling_median

            heading("WAITING FOR MANUAL ACTIVATION")

            wait_reference = time.monotonic()
            deadline = wait_reference + 300.0

            while time.monotonic() < deadline:
                state, _ = await sample(
                    "WAIT_MANUAL",
                    wait_reference,
                )

                if (
                    state["AppliedEnable"] is True
                    and int(state["AppliedDAC"]) > 0
                ):
                    break

                await asyncio.sleep(SAMPLE_S)
            else:
                raise RuntimeError(
                    "Timeout waiting for manual activation."
                )

            heading("RAMP TO 12000")

            ramp_reference = time.monotonic()
            deadline = ramp_reference + 30.0

            while time.monotonic() < deadline:
                state, _ = await sample(
                    "RAMP_12000",
                    ramp_reference,
                )

                if int(state["AppliedDAC"]) == 12000:
                    break

                await asyncio.sleep(SAMPLE_S)
            else:
                raise RuntimeError(
                    "AppliedDAC did not reach 12000."
                )

            print()
            print("AppliedDAC=12000: DETECTED")
            print(
                "At filtered PV 380..400, set "
                "RawPI.MANUAL_OUTPUT=2700."
            )

            heading("WAITING FOR 11700 STAGING")

            stage_reference = time.monotonic()
            deadline = stage_reference + 180.0
            stable_stage = 0
            stage_values: list[int] = []

            while time.monotonic() < deadline:
                state, _ = await sample(
                    "WAIT_STAGE",
                    stage_reference,
                )

                applied_dac = int(
                    state["AppliedDAC"]
                )

                if 11550 <= applied_dac <= 11850:
                    stable_stage += 1
                    stage_values.append(applied_dac)
                else:
                    stable_stage = 0
                    stage_values.clear()

                if stable_stage >= 8:
                    break

                await asyncio.sleep(SAMPLE_S)
            else:
                raise RuntimeError(
                    "Stable 11700 staging was not detected."
                )

            stage_center = int(
                round(
                    statistics.median(stage_values)
                )
            )

            print()
            print(
                "Staging output detected near "
                f"{stage_center}."
            )
            print(
                "When RawPVFilter.PV_OUT is 420..450:"
            )
            print("  RawPI.MANUAL = FALSE")
            print(
                "Keep observing the physical process."
            )

            heading("WAITING FOR AUTOMATIC MODULATION")

            auto_detection_reference = (
                time.monotonic()
            )
            deadline = (
                auto_detection_reference
                + 180.0
            )
            automatic_detected = False
            modulation_samples = 0

            while time.monotonic() < deadline:
                state, _ = await sample(
                    "WAIT_AUTO",
                    auto_detection_reference,
                )

                applied_dac = int(
                    state["AppliedDAC"]
                )

                if (
                    state["AppliedEnable"] is True
                    and abs(
                        applied_dac - stage_center
                    ) >= 150
                ):
                    modulation_samples += 1
                else:
                    modulation_samples = 0

                if modulation_samples >= 3:
                    automatic_detected = True
                    break

                await asyncio.sleep(SAMPLE_S)

            if not automatic_detected:
                raise RuntimeError(
                    "Automatic modulation was not detected."
                )

            print()
            print("Automatic modulation: DETECTED")
            print(
                "Automatic observation will run for "
                "30 seconds."
            )

            heading("AUTOMATIC OBSERVATION")

            auto_reference = time.monotonic()
            deadline = auto_reference + 30.0
            automatic_values: list[int] = []

            while time.monotonic() < deadline:
                state, _ = await sample(
                    "AUTO_ACTIVE",
                    auto_reference,
                )

                if state["AppliedEnable"] is not True:
                    raise RuntimeError(
                        "Applied output disabled before "
                        "the planned return sequence."
                    )

                automatic_values.append(
                    int(state["AppliedDAC"])
                )

                await asyncio.sleep(SAMPLE_S)

            automatic_range = (
                max(automatic_values)
                - min(automatic_values)
            )

            if automatic_range < 300:
                raise RuntimeError(
                    "Automatic DAC range was too small: "
                    f"{automatic_range}."
                )

            print()
            print(
                "Automatic DAC range: "
                f"{automatic_range}"
            )
            print()
            print("END THE TEST NOW:")
            print(
                "1. Set RawPI.MANUAL_OUTPUT=-9000."
            )
            print("2. Then set RawPI.MANUAL=TRUE.")
            print(
                "3. Reactivate the physical stop "
                "when flow stops."
            )
            print()
            shutdown_confirmation = input(
                "Depois de aplicar os dois valores no "
                "4diac, digite RETURN_ZERO_APPLIED: "
            ).strip()

            if shutdown_confirmation != "RETURN_ZERO_APPLIED":
                raise RuntimeError(
                    "The manual zero-return command "
                    "was not confirmed."
                )

            heading("WAITING FOR APPLIED OUTPUT DISABLE")

            disable_reference = time.monotonic()
            disable_deadline = disable_reference + 12.0
            immediate_disable_seen = False

            while time.monotonic() < disable_deadline:
                state, _ = await sample(
                    "DISABLE_OUTPUT",
                    disable_reference,
                )

                applied_zero = (
                    state["AppliedEnable"] is False
                    and int(state["AppliedDAC"]) == 0
                )

                if applied_zero:
                    immediate_disable_seen = True
                    break

                await asyncio.sleep(SAMPLE_S)
            else:
                raise RuntimeError(
                    "Applied output did not disable "
                    "after the confirmed manual command."
                )

            heading("WAITING FOR COMPLETE COMMAND ZERO")

            zero_reference = time.monotonic()
            zero_deadline = zero_reference + 135.0
            stable_zero = 0

            while time.monotonic() < zero_deadline:
                state, _ = await sample(
                    "RETURN_ZERO",
                    zero_reference,
                )

                complete_zero = (
                    state["Enable"] is False
                    and int(state["DAC"]) == 0
                    and state["AppliedEnable"] is False
                    and int(state["AppliedDAC"]) == 0
                )

                if complete_zero:
                    stable_zero += 1
                else:
                    stable_zero = 0

                if stable_zero >= 8:
                    break

                await asyncio.sleep(SAMPLE_S)
            else:
                raise RuntimeError(
                    "Complete command zero was not "
                    "confirmed within 135 seconds."
                )

    if not immediate_disable_seen:
        raise RuntimeError(
            "Immediate applied-output disable "
            "was not observed."
        )

    final_confirmation = input(
        "Digite STOP_ACTIVE_FLOW_STOPPED para "
        "confirmar parada fisica ativa e fluxo parado: "
    ).strip()

    if final_confirmation != "STOP_ACTIVE_FLOW_STOPPED":
        raise RuntimeError(
            "Physical stop and stopped flow "
            "were not confirmed."
        )

    heading("TUNED PI TEST RESULT")

    print(f"CSV: {csv_path}")
    print("Manual ramp to 12000: PASSED")
    print("11700 staging: PASSED")
    print("Automatic modulation: PASSED")
    print("Immediate applied-output disable: PASSED")
    print("Complete command return to zero: PASSED")
    print("Physical stop active: CONFIRMED")
    print()
    print("ETAPA 6.9F completed successfully.")
    print("TUNED PI FUNCTIONAL TEST: PASSED")
    print("READY FOR RESULT REVIEW: YES")
    print("READY TO STOP STACK: YES")


async def command_stop() -> None:
    confirmation = input(
        "Digite STOP_ACTIVE para confirmar "
        "a parada fisica ativa: "
    ).strip()

    if confirmation != "STOP_ACTIVE":
        raise RuntimeError(
            "Physical stop was not confirmed."
        )

    heading("CONTROLLED STACK STOP")

    stop_related_processes()

    try:
        await write_safe_plc_commands()
    except Exception as error:
        print(
            "Direct safe command warning: "
            f"{error!r}"
        )

    await asyncio.sleep(0.8)

    wait_port(
        "127.0.0.1",
        4841,
        False,
        10.0,
    )
    wait_port(
        "127.0.0.1",
        61499,
        False,
        10.0,
    )

    await validate_plc_safe_trip()

    print()
    print("STACK STOP: PASSED")
    print("FINAL PLC SAFE TRIP: PASSED")
    print("ETAPA 6.9F SAFE CLOSURE: PASSED")


async def dispatch(command: str) -> None:
    if command == "preflight":
        await command_preflight()
        return

    if command == "start":
        await command_start()
        return

    if command == "monitor":
        try:
            await command_monitor()
        except Exception as error:
            await emergency_stop(str(error))
            raise
        return

    if command == "stop":
        await command_stop()
        return

    raise RuntimeError(
        f"Unknown command: {command}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Managed real-plant tuned PI test "
            "for PI_REAL_RAW_SAFE."
        )
    )
    parser.add_argument(
        "command",
        choices=(
            "preflight",
            "start",
            "monitor",
            "stop",
        ),
    )
    arguments = parser.parse_args()

    try:
        asyncio.run(
            dispatch(arguments.command)
        )
    except KeyboardInterrupt:
        print()
        print("Interrupted by the user.")

        if arguments.command in {
            "monitor",
            "start",
        }:
            asyncio.run(
                emergency_stop(
                    "User interruption."
                )
            )

        raise SystemExit(130)
    except Exception as error:
        print()
        print(
            f"FAILED: {error}"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
