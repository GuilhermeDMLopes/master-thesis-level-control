from __future__ import annotations

import ast
import csv
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FBT = ROOT / "4diac/application/OPAS_Tank_System/Type Library/net_custom/MPC_MOVE_BLOCKED_NMPC_V4.fbt"
SYSTEM = ROOT / "4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys"
MODEL = ROOT / "models/mpc/high-range-hammerstein-v4-candidate.json"
EXECUTOR = ROOT / "scripts/mpc_high_range_validation.py"


def test_v4_files_exist():
    for path in (FBT, SYSTEM, MODEL, EXECUTOR):
        assert path.is_file(), path


def test_v4_fbt_contract():
    root = ET.parse(FBT).getroot()
    assert root.attrib["Name"] == "MPC_MOVE_BLOCKED_NMPC_V4"
    version = root.find("VersionInfo")
    assert version is not None
    assert version.attrib["Version"] == "4.0"
    source = FBT.read_text(encoding="utf-8")
    for token in (
        "LREAL#16000.0",
        "LREAL#18000.0",
        "LREAL#19500.0",
        "LREAL#20000.0",
        "LREAL#0.997231776304349",
        "LREAL#0.004607840412330",
        "FOR candidate_index := 0 TO 10 DO",
        "FOR prediction_index := 1 TO 60 DO",
        "delayed_u := predicted_u",
    ):
        assert token in source


def test_v4_application_and_resource_are_additive():
    source = SYSTEM.read_text(encoding="utf-8")
    for historical in (
        "MPC_REAL_RAW_SAFE_V3H",
        "ResRealRawMPCV3H",
        "MPC_MOVE_BLOCKED_NMPC_V3H",
    ):
        assert historical in source
    for final in (
        "MPC_REAL_RAW_SAFE_V4",
        "ResRealRawMPCV4",
        "MPC_MOVE_BLOCKED_NMPC_V4",
    ):
        assert final in source
    app = re.search(
        r'<Application Name="MPC_REAL_RAW_SAFE_V4".*?</Application>',
        source,
        re.DOTALL,
    )
    assert app is not None
    assert 'Name="SP_RAW" Value="LREAL#17000.0"' in app.group(0)
    assert 'Name="DAC_MAX" Value="LREAL#16000.0"' in app.group(0)


def test_high_range_model_replays_preserved_transients():
    model = json.loads(MODEL.read_text(encoding="utf-8"))["fit_500ms"]
    root = ROOT / "data/sample/m3-level-calibration-20260825"
    squared = []
    for name in (
        "point-03cm-samples.csv",
        "point-05cm-samples.csv",
        "point-08_5cm-samples.csv",
        "point-13cm-samples.csv",
    ):
        with (root / name).open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        # Replay at the original irregular timestamps. A nine-sample median is
        # intentionally not reconstructed here; the looser bound includes raw
        # sensor noise while still rejecting the obsolete low-range dynamics.
        y = float(rows[0]["level_raw"])
        previous_t = float(rows[0]["elapsed_s"])
        for row in rows[1:]:
            now = float(row["elapsed_s"])
            dt = now - previous_t
            a = math.exp(-dt / float(model["tau_s"]))
            u = float(row["applied_dac"])
            phi = max(0.0, u - float(model["deadzone_DAC"])) ** float(
                model["input_exponent_p"]
            )
            equilibrium = float(model["offset_raw"]) + float(
                model["static_gain"]
            ) * phi
            y = a * y + (1.0 - a) * equilibrium
            observed = float(row["level_raw"])
            squared.append((y - observed) ** 2)
            previous_t = now
    rmse = math.sqrt(sum(squared) / len(squared))
    assert rmse < 350.0


def test_high_range_executor_defaults_and_guards():
    source = EXECUTOR.read_text(encoding="utf-8")
    assert "HIGH_RANGE_MPC_READY" in source
    assert "ResRealRawMPCV4" in source
    assert "SP_RAW = 17000.0" in source
    assert "maximum DAC must be in 1..16000" in source
    assert "high-range duration must not exceed 240 s" in source
    tree = ast.parse(source)
    assert tree is not None
    for forbidden in (
        "write_value(True",
        "Variant(True",
        "write_value(16000",
        "Variant(16000",
    ):
        assert forbidden not in source


def test_high_range_plan_is_offline_and_pinned():
    result = subprocess.run(
        [sys.executable, str(EXECUTOR), "--plan"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert "Active window: 180.0 s" in output
    assert "Maximum DAC: 16000.0" in output
    assert "Maximum rolling-median raw: 19000.0" in output
    assert "Maximum instantaneous raw: 20000.0" in output
    assert "500.0 raw/s" in output
