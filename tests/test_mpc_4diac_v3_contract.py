from __future__ import annotations

from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "4diac" / "application" / "OPAS_Tank_System"
SYSTEM = PROJECT / "OPAS_Tank_System.sys"
V1 = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V1.fbt"
V2 = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V2.fbt"
V3 = PROJECT / "Type Library" / "net_custom" / "MPC_MOVE_BLOCKED_NMPC_V3.fbt"
HISTORICAL = PROJECT / "MPC_LEVEL.fbt"

APP_V1 = "MPC_REAL_RAW_SAFE_V1"
APP_V2 = "MPC_REAL_RAW_SAFE_V2"
APP_V3 = "MPC_REAL_RAW_SAFE_V3"
RES_V1 = "ResRealRawMPCV1"
RES_V2 = "ResRealRawMPCV2"
RES_V3 = "ResRealRawMPCV3"


def parse(path: Path):
    return ET.parse(path).getroot()


def one_app(root, name):
    matches = [
        app for app in root.findall("Application")
        if app.get("Name") == name
    ]
    assert len(matches) == 1
    return matches[0]


def one_device(root):
    matches = [
        dev for dev in root.findall("Device")
        if dev.get("Name") == "FORTE_PC"
    ]
    assert len(matches) == 1
    return matches[0]


def one_res(root, name):
    matches = [
        res for res in one_device(root).findall("Resource")
        if res.get("Name") == name
    ]
    assert len(matches) == 1
    return matches[0]


def fb_map(network):
    return {
        fb.get("Name"): fb
        for fb in network.findall("FB")
    }


def params(fb):
    return {
        p.get("Name"): p.get("Value")
        for p in fb.findall("Parameter")
    }


def events(network):
    return {
        (c.get("Source"), c.get("Destination"))
        for c in network.findall("./EventConnections/Connection")
    }


def signature(element):
    meaningful = None
    if element.text is not None and element.text.strip():
        meaningful = element.text.strip()
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        meaningful,
        tuple(signature(child) for child in list(element)),
    )


def baseline_system():
    relative = "4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys"
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return ET.fromstring(result.stdout)


def test_v3_fbt_xml_and_interface_are_additive():
    v2 = parse(V2)
    v3 = parse(V3)

    assert v3.get("Name") == "MPC_MOVE_BLOCKED_NMPC_V3"

    v2_interface = v2.find("InterfaceList")
    v3_interface = v3.find("InterfaceList")
    assert v2_interface is not None
    assert v3_interface is not None

    # Event comment is allowed to change; interface names/types/With lists must match.
    def interface_semantics(interface):
        return (
            [
                (
                    e.get("Name"),
                    e.get("Type"),
                    tuple(w.get("Var") for w in e.findall("With")),
                )
                for e in interface.findall("./EventInputs/Event")
            ],
            [
                (
                    e.get("Name"),
                    e.get("Type"),
                    tuple(w.get("Var") for w in e.findall("With")),
                )
                for e in interface.findall("./EventOutputs/Event")
            ],
            [
                (v.get("Name"), v.get("Type"))
                for v in interface.findall("./InputVars/VarDeclaration")
            ],
            [
                (v.get("Name"), v.get("Type"))
                for v in interface.findall("./OutputVars/VarDeclaration")
            ],
        )

    assert interface_semantics(v3_interface) == interface_semantics(v2_interface)


def test_v3_internal_delay_queue_is_exactly_18_plus_18_scalars():
    root = parse(V3)
    names = {
        var.get("Name")
        for var in root.findall("./BasicFB/InternalVars/VarDeclaration")
    }

    history = {f"h{i:02d}" for i in range(18)}
    prediction = {f"q{i:02d}" for i in range(18)}

    assert history <= names
    assert prediction <= names
    assert "history_count" in names
    assert "record_history_internal" in names
    assert "candidate_index" in names

    assert not any(
        name is not None and re.fullmatch(r"h\d\d", name) and name not in history
        for name in names
    )
    assert not any(
        name is not None and re.fullmatch(r"q\d\d", name) and name not in prediction
        for name in names
    )


def test_v3_st_has_13_candidates_and_60_step_delay_aware_prediction():
    st = parse(V3).findtext("./BasicFB/Algorithm/ST") or ""

    # Exporter-safe representation: one outer candidate loop and one
    # nested prediction loop. The 13 candidate values are assigned by CASE.
    assert st.count("FOR candidate_index := 0 TO 12 DO") == 1
    assert st.count("FOR prediction_index := 1 TO 60 DO") == 1
    assert "CASE candidate_index OF" in st

    # 13 CASE candidates plus one defensive ELSE assignment.
    assert st.count("candidate_target :=") == 14

    assert "delayed_u := q00;" in st
    assert "q00 := q01;" in st
    assert "q16 := q17;" in st
    assert "q17 := predicted_u;" in st

    assert "h00 := h01;" in st
    assert "h16 := h17;" in st
    assert "h17 := APPLIED_DAC;" in st
    assert "history_count < 18" in st


def test_v3_uses_identified_delayed_dynamic_parameters():
    st = parse(V3).findtext("./BasicFB/Algorithm/ST") or ""

    assert "LREAL#288.0" in st
    assert "LREAL#0.900087626252259" in st
    assert "LREAL#0.067989118863552" in st
    assert "LREAL#11750.0" in st

    assert "LREAL#0.984496437005408" not in st
    assert "LREAL#0.010549980424939" not in st
    assert "LREAL#298.0" not in st


def test_v3_bias_adaptation_is_disabled():
    root = parse(V3)
    st = root.findtext("./BasicFB/Algorithm/ST") or ""
    internal_names = {
        v.get("Name")
        for v in root.findall("./BasicFB/InternalVars/VarDeclaration")
    }

    assert "input_bias_internal" not in internal_names
    assert "bias_update" not in internal_names
    assert "sensitivity" not in internal_names
    assert "INPUT_BIAS_ESTIMATE_DAC := LREAL#0.0;" in st


def test_v3_safety_and_move_envelope_remain_frozen():
    st = parse(V3).findtext("./BasicFB/Algorithm/ST") or ""

    assert "LREAL#750.0" in st
    assert "LREAL#-750.0" in st
    assert "LREAL#12000.0" in st
    assert "LREAL#650.0" in st
    assert "LREAL#800.0" in st
    assert "history_count < 18" in st
    assert "trip_code_internal := 7;" in st

    assert "LREAL#5.0 * tracking_error * tracking_error" in st
    assert "LREAL#0.00004 * move_value * move_value" in st
    assert "LREAL#100.0 * soft_excess * soft_excess" in st
    assert "LREAL#10.0 * terminal_error * terminal_error" in st


def test_v3_st_remains_forte_exporter_literal_compatible():
    st = parse(V3).findtext("./BasicFB/Algorithm/ST") or ""

    typed_integer_lreal = re.findall(
        r"\bLREAL#[+-]?\d+(?![\d.])",
        st,
    )
    typed_scientific_lreal = re.findall(
        r"\bLREAL#[+-]?\d+(?:\.\d+)?[Ee][+-]?\d+",
        st,
    )

    assert typed_integer_lreal == []
    assert typed_scientific_lreal == []


def test_v3_application_and_resource_preserve_v2_outer_contract():
    root = parse(SYSTEM)

    expected_names = {
        "MpcLevelRead",
        "MpcMedian9",
        "MpcAppliedDACRead",
        "MpcAppliedDACType",
        "MpcWatchdogRead",
        "MpcController",
        "MpcSafeDACLimiter",
        "MpcDACType",
        "MpcDACWrite",
        "MpcEnableWrite",
        "MpcInitMerge",
        "MpcCycle",
    }

    for label, network in (
        ("APPLICATION", one_app(root, APP_V3).find("SubAppNetwork")),
        ("RESOURCE", one_res(root, RES_V3).find("FBNetwork")),
    ):
        assert network is not None
        fbs = fb_map(network)

        assert set(fbs) == expected_names
        assert fbs["MpcController"].get("Type") == "MPC_MOVE_BLOCKED_NMPC_V3"
        assert fbs["MpcCycle"].get("Type") == "E_CYCLE"
        assert params(fbs["MpcCycle"])["DT"] == "T#500ms"

        limiter = params(fbs["MpcSafeDACLimiter"])
        assert limiter["MAX_DELTA_DAC"] == "LREAL#750.0"
        assert limiter["DAC_MIN"] == "LREAL#0.0"
        assert limiter["DAC_MAX"] == "LREAL#12000.0"

        controller = params(fbs["MpcController"])
        assert controller["ENABLE_REQUEST"] == "FALSE"
        assert controller["RESET_REQUEST"] == "FALSE"
        assert controller["SP_RAW"] in ("450", "450.0", "LREAL#450.0")

        event_set = events(network)
        assert ("MpcLevelRead.INITO", "MpcCycle.START") in event_set
        assert ("MpcCycle.EO", "MpcMedian9.REQ") in event_set
        assert ("MpcLevelRead.IND", "MpcMedian9.REQ") not in event_set

        if label == "RESOURCE":
            assert not any(
                (source or "").startswith("START.")
                for source, _ in event_set
            )


def test_v3_opcua_ids_and_complete_mapping_are_preserved():
    root = parse(SYSTEM)

    expected_ids = {
        "MpcLevelRead":
            '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=Nivel]"',
        "MpcAppliedDACRead":
            '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=AppliedDAC]"',
        "MpcWatchdogRead":
            '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=WatchdogHealthy]"',
        "MpcDACWrite":
            '"opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=DAC]"',
        "MpcEnableWrite":
            '"opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=Enable]"',
    }

    app_network = one_app(root, APP_V3).find("SubAppNetwork")
    res_network = one_res(root, RES_V3).find("FBNetwork")
    assert app_network is not None
    assert res_network is not None

    for network in (app_network, res_network):
        fbs = fb_map(network)
        for name, expected in expected_ids.items():
            assert params(fbs[name])["ID"] == expected

    app_names = set(fb_map(app_network))
    res_names = set(fb_map(res_network))
    assert app_names == res_names

    mappings = {
        (m.get("From"), m.get("To"))
        for m in root.findall("Mapping")
    }

    for name in app_names:
        assert (
            f"{APP_V3}.{name}",
            f"FORTE_PC.{RES_V3}.{name}",
        ) in mappings


def test_v1_and_v2_application_resource_semantics_match_head():
    current = parse(SYSTEM)
    baseline = baseline_system()

    for app_name in (APP_V1, APP_V2):
        assert signature(one_app(current, app_name)) == signature(
            one_app(baseline, app_name)
        )

    for res_name in (RES_V1, RES_V2):
        assert signature(one_res(current, res_name)) == signature(
            one_res(baseline, res_name)
        )


def test_v1_v2_and_historical_fbt_content_match_head_ignoring_line_endings():
    for path in (V1, V2, HISTORICAL):
        relative = path.relative_to(ROOT).as_posix()
        baseline = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        working = path.read_bytes().replace(b"\r\n", b"\n")
        baseline = baseline.replace(b"\r\n", b"\n")
        assert working == baseline
