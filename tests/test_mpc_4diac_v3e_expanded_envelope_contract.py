from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SYS = ROOT / "4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys"
V3 = ROOT / (
    "4diac/application/OPAS_Tank_System/Type Library/net_custom/"
    "MPC_MOVE_BLOCKED_NMPC_V3.fbt"
)
V3E = ROOT / (
    "4diac/application/OPAS_Tank_System/Type Library/net_custom/"
    "MPC_MOVE_BLOCKED_NMPC_V3E.fbt"
)

GOOD_TYPE = "MPC_MOVE_BLOCKED_NMPC_V3E"
BAD_TYPE = "MPC_MOVE_BLOCKED_NMPC_V3EE"


def local_tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1]


def st_text(path: Path) -> str:
    tree = ET.parse(path)
    chunks = []

    for elem in tree.getroot().iter():
        if local_tag(elem).upper() != "ST":
            continue
        chunks.append(
            html.unescape(elem.attrib.get("Text", elem.text or ""))
        )

    return "\n".join(chunks)


def system_root() -> ET.Element:
    return ET.parse(SYS).getroot()


def unique_named(tag: str, name: str) -> ET.Element:
    matches = [
        elem
        for elem in system_root().iter()
        if local_tag(elem) == tag
        and elem.attrib.get("Name") == name
    ]

    assert len(matches) == 1, (
        f"Expected exactly one {tag} Name={name!r}, "
        f"found {len(matches)}"
    )
    return matches[0]


def values_for_name(root: ET.Element, name: str) -> list[str]:
    """
    4diac .sys parameter/default serialization can vary by element type/version.
    Read semantically relevant value-like attributes instead of assuming one
    textual representation such as InitialValue="...".
    """
    values: list[str] = []

    for elem in root.iter():
        if elem.attrib.get("Name") != name:
            continue

        for attr in (
            "InitialValue",
            "Value",
            "value",
            "DefaultValue",
            "Default",
        ):
            if attr in elem.attrib:
                values.append(elem.attrib[attr])

        if elem.text and elem.text.strip():
            values.append(elem.text.strip())

    return values


def normalize(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def test_v3e_exists_and_is_additive():
    assert V3.exists()
    assert V3E.exists()


def test_v3e_type_name_is_exact_not_v3ee():
    root = ET.parse(V3E).getroot()
    assert root.attrib["Name"] == GOOD_TYPE
    assert BAD_TYPE not in V3E.read_text(encoding="utf-8")


def test_v3e_expanded_thresholds():
    st = st_text(V3E)

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


def test_old_v3_trip_thresholds_absent_from_v3e_conditions():
    st = st_text(V3E)

    assert not re.search(
        r"\bpredicted_y\b\s*>\s*(?:LREAL#)?650(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )
    assert not re.search(
        r"\bpredicted_y\b\s*>\s*(?:LREAL#)?750(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )
    assert not re.search(
        r"\bPV_RAW\b\s*(?:>=|>)\s*(?:LREAL#)?800(?:\.0+)?\b",
        st,
        flags=re.IGNORECASE,
    )


def test_v3e_system_application_and_resource_exist_once():
    unique_named("Application", "MPC_REAL_RAW_SAFE_V3E")
    unique_named("Resource", "ResRealRawMPCV3E")


def test_v3e_has_exactly_12_mappings():
    text = SYS.read_text(encoding="utf-8")

    assert text.count('From="MPC_REAL_RAW_SAFE_V3E.') == 12
    assert text.count('To="FORTE_PC.ResRealRawMPCV3E.') == 12


def test_v3e_system_uses_exact_v3e_controller_type():
    text = SYS.read_text(encoding="utf-8")

    assert GOOD_TYPE in text
    assert BAD_TYPE not in text


def test_original_v3_artifacts_still_present():
    unique_named("Application", "MPC_REAL_RAW_SAFE_V3")
    unique_named("Resource", "ResRealRawMPCV3")

    assert V3.exists()
    assert ET.parse(V3).getroot().attrib["Name"] == "MPC_MOVE_BLOCKED_NMPC_V3"


def test_v3e_default_enable_request_is_false_semantically():
    app = unique_named("Application", "MPC_REAL_RAW_SAFE_V3E")
    values = [normalize(v) for v in values_for_name(app, "ENABLE_REQUEST")]

    assert values, "No value representation found for ENABLE_REQUEST"
    assert "FALSE" in values


def test_v3e_cycle_is_500ms_semantically():
    app = unique_named("Application", "MPC_REAL_RAW_SAFE_V3E")
    values = [normalize(v) for v in values_for_name(app, "DT")]

    assert values, "No value representation found for DT"
    assert "T#500MS" in values


def test_v3e_limiter_move_remains_750_semantically():
    app = unique_named("Application", "MPC_REAL_RAW_SAFE_V3E")
    values = [
        normalize(v)
        for v in values_for_name(app, "MAX_DELTA_DAC")
    ]

    assert values, "No value representation found for MAX_DELTA_DAC"
    assert any(
        re.fullmatch(r"(?:LREAL#|REAL#)?750(?:\.0+)?", value)
        for value in values
    )


def test_v3e_controller_period_and_envelope_do_not_change_model_constants():
    v3 = st_text(V3)
    v3e = st_text(V3E)

    # Core identified model/delay constants must remain represented in both.
    for token in (
        "0.900087626252259",
        "0.067989118863552",
    ):
        assert token in v3
        assert token in v3e

    # Queue/prediction implementation remains the nested-loop V3 structure.
    for token in (
        "candidate_index",
        "prediction_index",
        "history_count",
    ):
        assert token in v3e
