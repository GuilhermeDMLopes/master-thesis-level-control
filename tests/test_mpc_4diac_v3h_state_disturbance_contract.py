from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "4diac/application/OPAS_Tank_System"

SYS = PROJECT / "OPAS_Tank_System.sys"
V3E = PROJECT / (
    "Type Library/net_custom/MPC_MOVE_BLOCKED_NMPC_V3E.fbt"
)
V3H = PROJECT / (
    "Type Library/net_custom/MPC_MOVE_BLOCKED_NMPC_V3H.fbt"
)

V3E_TYPE = "MPC_MOVE_BLOCKED_NMPC_V3E"
V3H_TYPE = "MPC_MOVE_BLOCKED_NMPC_V3H"

APP_V3E = "MPC_REAL_RAW_SAFE_V3E"
APP_V3H = "MPC_REAL_RAW_SAFE_V3H"

RES_V3E = "ResRealRawMPCV3E"
RES_V3H = "ResRealRawMPCV3H"


def local_tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1]


def parse(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def st_text(path: Path) -> str:
    root = parse(path)
    matches = [
        elem
        for elem in root.iter()
        if local_tag(elem).upper() == "ST"
    ]
    assert len(matches) == 1

    elem = matches[0]
    return html.unescape(elem.attrib.get("Text", elem.text or ""))


def internal_names(path: Path) -> set[str]:
    root = parse(path)
    return {
        elem.attrib["Name"]
        for elem in root.iter()
        if local_tag(elem) == "VarDeclaration"
        and "Name" in elem.attrib
    }


def named(root: ET.Element, tag: str, name: str) -> list[ET.Element]:
    return [
        elem
        for elem in root.iter()
        if local_tag(elem) == tag
        and elem.attrib.get("Name") == name
    ]


def candidate_assignments(st: str) -> list[str]:
    return re.findall(
        r"candidate_target\s*:=\s*([^;]+);",
        st,
    )


def test_v3h_exists_additively_and_type_is_exact():
    assert V3E.is_file()
    assert V3H.is_file()

    v3h = parse(V3H)
    assert v3h.attrib["Name"] == V3H_TYPE
    assert "MPC_MOVE_BLOCKED_NMPC_V3HH" not in V3H.read_text(
        encoding="utf-8"
    )


def test_v3h_adds_only_required_estimator_internal_state():
    names = internal_names(V3H)

    required = {
        "disturbance_hat_internal",
        "disturbance_previous_pv_internal",
        "disturbance_previous_valid_internal",
        "disturbance_prediction_internal",
        "disturbance_innovation_internal",
    }

    assert required <= names


def test_v3h_ewma_alpha_and_bounds_match_python_contract():
    st = st_text(V3H)

    assert (
        "LREAL#0.9 * disturbance_hat_internal "
        "+ LREAL#0.1 * disturbance_innovation_internal"
    ) in st
    assert "disturbance_hat_internal := LREAL#100.0;" in st
    assert "disturbance_hat_internal := LREAL#-100.0;" in st


def test_v3h_observer_uses_previous_pv_and_oldest_delay_history():
    st = st_text(V3H)

    assert "disturbance_previous_pv_internal := PV_MODEL;" in st
    assert "effective_input := h00" in st
    assert (
        "disturbance_innovation_internal := "
        "PV_MODEL - disturbance_prediction_internal;"
    ) in st


def test_v3h_resets_estimator_on_reset_and_disabled_state():
    st = st_text(V3H)

    # One reset in RESET_REQUEST and one in normal disabled state.
    assert st.count(
        "disturbance_hat_internal := LREAL#0.0;"
    ) >= 2
    assert st.count(
        "disturbance_previous_valid_internal := FALSE;"
    ) >= 2


def test_v3h_injects_disturbance_into_single_future_state_transition():
    st = st_text(V3H)

    assert st.count("+ disturbance_hat_internal;") == 1

    assert re.search(
        r"predicted_y\s*:=\s*"
        r"LREAL#288(?:\.0+)?\s*\+\s*"
        r"LREAL#0\.900087626252259\s*\*\s*"
        r"\(\s*predicted_y\s*-\s*LREAL#288(?:\.0+)?\s*\)\s*\+\s*"
        r"LREAL#0\.067989118863552\s*\*\s*phi_value\s*\+\s*"
        r"disturbance_hat_internal\s*;",
        st,
        flags=re.IGNORECASE | re.MULTILINE,
    )


def test_exporter_safe_nested_loop_structure_is_preserved():
    st = st_text(V3H)

    assert st.count("FOR candidate_index := 0 TO 12 DO") == 1
    assert st.count("FOR prediction_index := 1 TO 60 DO") == 1
    assert st.count("CASE candidate_index OF") == 1
    assert "history_count < 18" in st


def test_exact_canonical_target_assignments_are_preserved():
    assert candidate_assignments(st_text(V3H)) == candidate_assignments(
        st_text(V3E)
    )
    assert len(candidate_assignments(st_text(V3H))) == 14


def test_v3e_expanded_safety_envelope_is_preserved():
    st = st_text(V3H)

    assert re.search(
        r"\bpredicted_y\b\s*>\s*(?:LREAL#)?1100(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"\bpredicted_y\b\s*>\s*(?:LREAL#)?1400(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"\bPV_RAW\b\s*(?:>=|>)\s*(?:LREAL#)?1500(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )


def test_input_bias_output_is_not_repurposed():
    st = st_text(V3H)
    assert "INPUT_BIAS_ESTIMATE_DAC := LREAL#0.0;" in st


def test_v3h_system_application_resource_and_mappings_exist_once():
    root = parse(SYS)

    assert len(named(root, "Application", APP_V3H)) == 1
    assert len(named(root, "Resource", RES_V3H)) == 1

    text = SYS.read_text(encoding="utf-8")

    assert text.count(f'From="{APP_V3H}.') == 12
    assert text.count(f'To="FORTE_PC.{RES_V3H}.') == 12
    assert V3H_TYPE in text


def test_v3h_resource_has_no_automatic_start_connection():
    root = parse(SYS)
    resource = named(root, "Resource", RES_V3H)
    assert len(resource) == 1

    automatic = [
        elem
        for elem in resource[0].iter()
        if local_tag(elem) == "Connection"
        and (elem.attrib.get("Source") or "").startswith("START.")
    ]

    assert automatic == []


def test_source_v3e_application_and_resource_still_exist_once():
    root = parse(SYS)

    assert len(named(root, "Application", APP_V3E)) == 1
    assert len(named(root, "Resource", RES_V3E)) == 1
