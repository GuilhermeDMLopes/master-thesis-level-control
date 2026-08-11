from __future__ import annotations

from pathlib import Path
import hashlib
import math
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "4diac" / "application" / "OPAS_Tank_System"
SYSTEM = PROJECT / "OPAS_Tank_System.sys"
HISTORICAL_MPC = PROJECT / "MPC_LEVEL.fbt"
MEDIAN = PROJECT / "Type Library" / "net_custom" / "MPC_MEDIAN_FILTER_9.fbt"
NMPC = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V1.fbt"

APPLICATION = "MPC_REAL_RAW_SAFE_V1"
RESOURCE = "ResRealRawMPCV1"


def parse(path: Path):
    return ET.parse(path).getroot()


def find_application(root, name: str):
    matches = [item for item in root.findall("Application") if item.get("Name") == name]
    assert len(matches) == 1
    return matches[0]


def find_device(root, name: str):
    matches = [item for item in root.findall("Device") if item.get("Name") == name]
    assert len(matches) == 1
    return matches[0]


def fb_map(network):
    return {fb.get("Name"): fb for fb in network.findall("FB")}


def params(fb):
    return {p.get("Name"): p.get("Value") for p in fb.findall("Parameter")}


def connections(parent):
    return {(c.get("Source"), c.get("Destination")) for c in parent.findall("Connection")}


def test_new_types_are_additive_and_historical_mpc_remains_present():
    assert HISTORICAL_MPC.is_file()
    assert MEDIAN.is_file()
    assert NMPC.is_file()

    assert parse(MEDIAN).get("Name") == "MPC_MEDIAN_FILTER_9"
    assert parse(NMPC).get("Name") == "MPC_MOVE_BLOCKED_NMPC_V1"


def test_median_filter_contract():
    root = parse(MEDIAN)
    inputs = {v.get("Name"): v.get("Type") for v in root.findall("./InterfaceList/InputVars/VarDeclaration")}
    outputs = {v.get("Name"): v.get("Type") for v in root.findall("./InterfaceList/OutputVars/VarDeclaration")}
    assert inputs == {"PV_RAW": "LREAL", "RESET": "BOOL"}
    assert outputs == {"PV_MEDIAN": "LREAL", "INITIALIZED": "BOOL"}

    st = root.findtext("./BasicFB/Algorithm/ST") or ""
    assert "PV_MEDIAN := s4;" in st
    assert "v8 := PV_RAW;" in st


def test_nmpc_interface_and_frozen_limits():
    root = parse(NMPC)
    inputs = {v.get("Name"): v.get("Type") for v in root.findall("./InterfaceList/InputVars/VarDeclaration")}
    outputs = {v.get("Name"): v.get("Type") for v in root.findall("./InterfaceList/OutputVars/VarDeclaration")}

    assert inputs == {
        "PV_RAW": "LREAL",
        "PV_MODEL": "LREAL",
        "APPLIED_DAC": "LREAL",
        "ENABLE_REQUEST": "BOOL",
        "EXTERNAL_HEALTHY": "BOOL",
        "RESET_REQUEST": "BOOL",
        "SP_RAW": "LREAL",
    }

    for name in (
        "COMMAND_ENABLE",
        "COMMAND_DAC",
        "TRIPPED",
        "TRIP_CODE",
        "SELECTED_TARGET_DAC",
        "INPUT_BIAS_ESTIMATE_DAC",
        "PREDICTED_MAX_RAW",
        "PREDICTED_FINAL_RAW",
        "CONFIGURATION_VALID",
    ):
        assert name in outputs

    st = root.findtext("./BasicFB/Algorithm/ST") or ""
    for marker in (
        "PV_RAW >= LREAL#800.0",
        "APPLIED_DAC <= LREAL#12000.0",
        "delta_u > LREAL#150.0",
        "predicted_y <= LREAL#750.0",
        "predicted_y > LREAL#650.0",
        "input_bias_internal > LREAL#250.0",
        "FOR prediction_index := 1 TO 200 DO",
        "FOR candidate_index := 0 TO 12 DO",
    ):
        assert marker in st


def test_piecewise_power_approximation_is_small_over_commissioning_bias_range():
    knots = [0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0]
    values = [0.0, 109.33620739432779, 251.18864315095797, 408.61048911399905, 577.0799623628853, 754.2720420681452, 938.7403933595692, 1129.4880832415931, 1325.7816069359944, 1527.0561856222143, 1732.8621078878655]

    def approx(x: float) -> float:
        x = max(0.0, min(500.0, x))
        if x <= 0:
            return 0.0
        for i in range(len(knots)-1):
            if x <= knots[i+1]:
                slope = (values[i+1]-values[i])/(knots[i+1]-knots[i])
                return values[i] + slope*(x-knots[i])
        return values[-1]

    errors = [
        abs(approx(i/10.0) - (i/10.0)**1.2)
        for i in range(0, 5001)
    ]
    assert max(errors) < 8.0


def test_model_constants_match_offline_checkpoint():
    st = parse(NMPC).findtext("./BasicFB/Algorithm/ST") or ""
    assert "LREAL#0.996879877730208" in st
    assert "LREAL#0.00212320412289765" in st
    assert "LREAL#11750.0" in st
    assert "LREAL#298.0" in st


def test_system_contains_exactly_one_additive_mpc_application_and_resource():
    root = parse(SYSTEM)
    app = find_application(root, APPLICATION)
    device = find_device(root, "FORTE_PC")

    resources = [r for r in device.findall("Resource") if r.get("Name") == RESOURCE]
    assert len(resources) == 1

    app_fbs = fb_map(app.find("SubAppNetwork"))
    res_fbs = fb_map(resources[0].find("FBNetwork"))
    expected = {
        "MpcLevelRead": "SUBSCRIBE_1",
        "MpcMedian9": "MPC_MEDIAN_FILTER_9",
        "MpcAppliedDACRead": "SUBSCRIBE_1",
        "MpcAppliedDACType": "F_INT_TO_LREAL",
        "MpcWatchdogRead": "SUBSCRIBE_1",
        "MpcController": "MPC_MOVE_BLOCKED_NMPC_V1",
        "MpcSafeDACLimiter": "SAFE_DAC_RATE_LIMITER",
        "MpcDACType": "F_LREAL_TO_INT",
        "MpcDACWrite": "CLIENT_1_0",
        "MpcEnableWrite": "CLIENT_1_0",
        "MpcInitMerge": "E_MERGE",
    }

    assert {name: fb.get("Type") for name, fb in app_fbs.items()} == expected
    assert {name: fb.get("Type") for name, fb in res_fbs.items()} == expected


def test_application_starts_disabled_and_uses_gateway_feedback_nodes():
    root = parse(SYSTEM)
    app = find_application(root, APPLICATION)
    fbs = fb_map(app.find("SubAppNetwork"))

    assert params(fbs["MpcController"]) == {
        "ENABLE_REQUEST": "FALSE",
        "RESET_REQUEST": "FALSE",
        "SP_RAW": "LREAL#450.0",
    }

    assert params(fbs["MpcAppliedDACRead"])["ID"] == '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;2:s=AppliedDAC]"'
    assert params(fbs["MpcWatchdogRead"])["ID"] == '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;2:s=WatchdogHealthy]"'
    assert params(fbs["MpcLevelRead"])["ID"] == '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;2:s=Nivel]"'


def test_application_matches_identified_model_coordinate_and_applied_dac_contract():
    root = parse(SYSTEM)
    app = find_application(root, APPLICATION)
    network = app.find("SubAppNetwork")
    data = connections(network.find("DataConnections"))

    required = {
        ("MpcLevelRead.RD_1", "MpcMedian9.PV_RAW"),
        ("MpcLevelRead.RD_1", "MpcController.PV_RAW"),
        ("MpcMedian9.PV_MEDIAN", "MpcController.PV_MODEL"),
        ("MpcAppliedDACRead.RD_1", "MpcAppliedDACType.IN"),
        ("MpcAppliedDACType.OUT", "MpcController.APPLIED_DAC"),
        ("MpcWatchdogRead.RD_1", "MpcController.EXTERNAL_HEALTHY"),
    }
    assert required.issubset(data)


def test_downstream_defense_in_depth_is_frozen_to_12000_and_150():
    root = parse(SYSTEM)
    app = find_application(root, APPLICATION)
    fbs = fb_map(app.find("SubAppNetwork"))

    assert params(fbs["MpcSafeDACLimiter"]) == {
        "MAX_DELTA_DAC": "LREAL#150.0",
        "DAC_MIN": "LREAL#0.0",
        "DAC_MAX": "LREAL#12000.0",
        "INITIAL_DAC": "LREAL#0.0",
        "RESET": "FALSE",
    }


def test_mpc_resource_has_no_automatic_start_connection():
    root = parse(SYSTEM)
    device = find_device(root, "FORTE_PC")
    resource = [r for r in device.findall("Resource") if r.get("Name") == RESOURCE][0]
    events = connections(resource.find("FBNetwork").find("EventConnections"))

    for source, destination in events:
        assert not source.startswith("START.")
        assert destination != "MpcInitMerge.EI1"
        assert destination != "MpcInitMerge.EI2"


def test_all_new_application_fbs_are_mapped_to_dedicated_resource():
    root = parse(SYSTEM)
    mappings = {
        (m.get("From"), m.get("To"))
        for m in root.findall("Mapping")
    }
    app = find_application(root, APPLICATION)
    names = fb_map(app.find("SubAppNetwork")).keys()

    for name in names:
        assert (
            f"{APPLICATION}.{name}",
            f"FORTE_PC.{RESOURCE}.{name}",
        ) in mappings


def test_pi_real_raw_safe_still_exists():
    root = parse(SYSTEM)
    names = [item.get("Name") for item in root.findall("Application")]
    assert "PI_REAL_RAW_SAFE" in names
    assert APPLICATION in names


def test_historical_mpc_level_is_not_replaced_by_new_type():
    historical = parse(HISTORICAL_MPC)
    new = parse(NMPC)
    assert historical.get("Name") == "MPC_LEVEL"
    assert new.get("Name") == "MPC_MOVE_BLOCKED_NMPC_V1"
