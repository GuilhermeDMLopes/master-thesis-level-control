from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "4diac" / "application" / "OPAS_Tank_System"
SYSTEM = PROJECT / "OPAS_Tank_System.sys"
V1 = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V1.fbt"
V2 = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V2.fbt"

APP_V1 = "MPC_REAL_RAW_SAFE_V1"
APP_V2 = "MPC_REAL_RAW_SAFE_V2"
RES_V1 = "ResRealRawMPCV1"
RES_V2 = "ResRealRawMPCV2"


def parse(path: Path):
    return ET.parse(path).getroot()


def find_app(root, name):
    matches = [
        app for app in root.findall("Application")
        if app.get("Name") == name
    ]
    assert len(matches) == 1
    return matches[0]


def find_resource(root, name):
    devices = [
        dev for dev in root.findall("Device")
        if dev.get("Name") == "FORTE_PC"
    ]
    assert len(devices) == 1
    matches = [
        res for res in devices[0].findall("Resource")
        if res.get("Name") == name
    ]
    assert len(matches) == 1
    return matches[0]


def fb_map(network):
    return {fb.get("Name"): fb for fb in network.findall("FB")}


def params(fb):
    return {
        p.get("Name"): p.get("Value")
        for p in fb.findall("Parameter")
    }


def event_set(network):
    return {
        (c.get("Source"), c.get("Destination"))
        for c in network.findall("./EventConnections/Connection")
    }


def test_v1_and_v2_fb_types_coexist():
    assert parse(V1).get("Name") == "MPC_MOVE_BLOCKED_NMPC_V1"
    assert parse(V2).get("Name") == "MPC_MOVE_BLOCKED_NMPC_V2"


def test_v2_interface_matches_v1():
    def interface(root):
        return (
            [
                (v.get("Name"), v.get("Type"))
                for v in root.findall(
                    "./InterfaceList/InputVars/VarDeclaration"
                )
            ],
            [
                (v.get("Name"), v.get("Type"))
                for v in root.findall(
                    "./InterfaceList/OutputVars/VarDeclaration"
                )
            ],
            [
                e.get("Name")
                for e in root.findall(
                    "./InterfaceList/EventInputs/Event"
                )
            ],
            [
                e.get("Name")
                for e in root.findall(
                    "./InterfaceList/EventOutputs/Event"
                )
            ],
        )

    assert interface(parse(V2)) == interface(parse(V1))


def test_v2_uses_40_step_500ms_model():
    st = parse(V2).findtext("./BasicFB/Algorithm/ST") or ""

    assert re.search(
        r"FOR\s+prediction_index\s*:=\s*1\s+TO\s+40"
        r"(?:\s+BY\s+1)?\s+DO",
        st,
    )
    assert not re.search(
        r"FOR\s+prediction_index\s*:=\s*1\s+TO\s+200"
        r"(?:\s+BY\s+1)?\s+DO",
        st,
    )

    assert st.count("LREAL#0.984496437005408") == 2
    assert st.count("LREAL#0.010549980424939") == 3
    assert "LREAL#0.996879877730208" not in st
    assert "LREAL#0.00212320412289765" not in st


def test_v2_move_limit_is_750():
    st = parse(V2).findtext("./BasicFB/Algorithm/ST") or ""

    assert st.count("IF delta_u > LREAL#750.0 THEN") == 2
    assert st.count("delta_u := LREAL#750.0;") == 2
    assert st.count("ELSIF delta_u < LREAL#-750.0 THEN") == 2
    assert st.count("delta_u := LREAL#-750.0;") == 2


def test_v2_cost_scaling():
    st = parse(V2).findtext("./BasicFB/Algorithm/ST") or ""
    normalized = re.sub(r"\s+", " ", st)

    assert "LREAL#5.0 * tracking_error * tracking_error" in normalized
    assert "LREAL#0.00004 * move_value * move_value" in normalized

    soft = [
        statement
        for statement in normalized.split(";")
        if statement.count("soft_excess") == 2
        and "candidate_cost := candidate_cost" in statement
    ]
    assert len(soft) == 1
    assert "LREAL#100.0" in soft[0]
    assert "LREAL#20.0" not in soft[0]

    terminal = [
        statement
        for statement in normalized.split(";")
        if statement.count("terminal_error") == 2
        and "candidate_cost := candidate_cost" in statement
    ]
    assert len(terminal) == 1
    assert "LREAL#10.0" in terminal[0]


def test_v2_application_and_resource_contract():
    root = parse(SYSTEM)

    for network in (
        find_app(root, APP_V2).find("SubAppNetwork"),
        find_resource(root, RES_V2).find("FBNetwork"),
    ):
        fbs = fb_map(network)

        assert fbs["MpcController"].get("Type") == "MPC_MOVE_BLOCKED_NMPC_V2"
        assert fbs["MpcCycle"].get("Type") == "E_CYCLE"
        assert params(fbs["MpcCycle"])["DT"] == "T#500ms"

        limiter = params(fbs["MpcSafeDACLimiter"])
        assert limiter["MAX_DELTA_DAC"] == "LREAL#750.0"
        assert limiter["DAC_MIN"] == "LREAL#0.0"
        assert limiter["DAC_MAX"] == "LREAL#12000.0"

        controller = params(fbs["MpcController"])
        assert controller["ENABLE_REQUEST"] == "FALSE"
        assert controller["RESET_REQUEST"] == "FALSE"

        events = event_set(network)
        assert ("MpcLevelRead.INITO", "MpcCycle.START") in events
        assert ("MpcCycle.EO", "MpcMedian9.REQ") in events
        assert ("MpcLevelRead.IND", "MpcMedian9.REQ") not in events


def test_v2_resource_has_no_automatic_start():
    root = parse(SYSTEM)
    network = find_resource(root, RES_V2).find("FBNetwork")

    for source, destination in event_set(network):
        assert not (source or "").startswith("START."), (
            source,
            destination,
        )


def test_v1_timing_contract_remains_unchanged():
    root = parse(SYSTEM)

    for network in (
        find_app(root, APP_V1).find("SubAppNetwork"),
        find_resource(root, RES_V1).find("FBNetwork"),
    ):
        fbs = fb_map(network)
        assert fbs["MpcController"].get("Type") == "MPC_MOVE_BLOCKED_NMPC_V1"
        assert params(fbs["MpcCycle"])["DT"] == "T#100ms"
        assert (
            params(fbs["MpcSafeDACLimiter"])["MAX_DELTA_DAC"]
            == "LREAL#150.0"
        )


def test_v2_has_complete_application_resource_mapping():
    root = parse(SYSTEM)
    app_network = find_app(root, APP_V2).find("SubAppNetwork")
    res_network = find_resource(root, RES_V2).find("FBNetwork")

    app_names = set(fb_map(app_network))
    res_names = set(fb_map(res_network))
    assert app_names == res_names

    mappings = {
        (m.get("From"), m.get("To"))
        for m in root.findall("Mapping")
    }

    for name in app_names:
        assert (
            f"{APP_V2}.{name}",
            f"FORTE_PC.{RES_V2}.{name}",
        ) in mappings
