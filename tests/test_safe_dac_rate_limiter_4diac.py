from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LIMITER_PATH = (
    REPOSITORY_ROOT
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
    / "Type Library"
    / "net_custom"
    / "SAFE_DAC_RATE_LIMITER.fbt"
)
HISTORICAL_LIMITER_PATH = (
    REPOSITORY_ROOT
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
    / "DAC_RATE_LIMITER.fbt"
)

EXPECTED_INPUTS = {
    "DAC_IN": "LREAL",
    "MAX_DELTA_DAC": "LREAL",
    "DAC_MIN": "LREAL",
    "DAC_MAX": "LREAL",
    "INITIAL_DAC": "LREAL",
    "RESET": "BOOL",
}

EXPECTED_OUTPUTS = {
    "DAC_OUT": "LREAL",
    "LIMITED": "BOOL",
    "INITIALIZED": "BOOL",
    "RESET_ACTIVE": "BOOL",
    "CONFIGURATION_VALID": "BOOL",
}

FORBIDDEN_PORTUGUESE_TERMS = {
    "entrada",
    "saída",
    "saida",
    "limite anterior",
    "reinicialização",
    "reinicializacao",
    "inicialização",
    "inicializacao",
}


def load_limiter() -> tuple[ET.Element, str]:
    xml_text = LIMITER_PATH.read_text(encoding="utf-8")
    return ET.fromstring(xml_text), xml_text


def declarations(
    root: ET.Element,
    section: str,
) -> dict[str, str]:
    section_element = root.find(f"./InterfaceList/{section}")
    assert section_element is not None

    return {
        declaration.attrib["Name"]: declaration.attrib["Type"]
        for declaration in section_element.findall("VarDeclaration")
    }


def algorithm_text(root: ET.Element) -> str:
    st_element = root.find(
        "./BasicFB/Algorithm"
        "[@Name='SAFE_DAC_RATE_LIMITER_ALGORITHM']/ST"
    )
    assert st_element is not None
    assert st_element.text is not None
    return st_element.text


def test_limiter_file_is_well_formed_and_additive() -> None:
    root, _ = load_limiter()

    assert root.attrib["Name"] == "SAFE_DAC_RATE_LIMITER"
    assert LIMITER_PATH.name == "SAFE_DAC_RATE_LIMITER.fbt"
    assert HISTORICAL_LIMITER_PATH.is_file()
    assert LIMITER_PATH != HISTORICAL_LIMITER_PATH


def test_limiter_interface_matches_the_specification() -> None:
    root, _ = load_limiter()

    assert declarations(root, "InputVars") == EXPECTED_INPUTS
    assert declarations(root, "OutputVars") == EXPECTED_OUTPUTS

    req = root.find("./InterfaceList/EventInputs/Event[@Name='REQ']")
    cnf = root.find("./InterfaceList/EventOutputs/Event[@Name='CNF']")

    assert req is not None
    assert cnf is not None

    assert [item.attrib["Var"] for item in req.findall("With")] == list(
        EXPECTED_INPUTS
    )
    assert [item.attrib["Var"] for item in cnf.findall("With")] == list(
        EXPECTED_OUTPUTS
    )


def test_limiter_ecc_executes_one_algorithm_and_confirmation() -> None:
    root, _ = load_limiter()

    state_names = {
        state.attrib["Name"]
        for state in root.findall("./BasicFB/ECC/ECState")
    }
    assert state_names == {"START", "CALCULATE", "CONFIRM"}

    transitions = {
        (
            transition.attrib["Source"],
            transition.attrib["Destination"],
            transition.attrib["Condition"],
        )
        for transition in root.findall("./BasicFB/ECC/ECTransition")
    }

    assert transitions == {
        ("START", "CALCULATE", "REQ"),
        ("CALCULATE", "CONFIRM", "1"),
        ("CONFIRM", "START", "1"),
    }

    calculate_action = root.find(
        "./BasicFB/ECC/ECState[@Name='CALCULATE']"
        "/ECAction[@Algorithm='SAFE_DAC_RATE_LIMITER_ALGORITHM']"
    )
    confirm_action = root.find(
        "./BasicFB/ECC/ECState[@Name='CONFIRM']"
        "/ECAction[@Output='CNF']"
    )

    assert calculate_action is not None
    assert confirm_action is not None


def test_algorithm_contains_configuration_and_safe_initialization() -> None:
    root, _ = load_limiter()
    algorithm = algorithm_text(root)

    required_fragments = (
        "MAX_DELTA_DAC > 0.0",
        "DAC_MIN < DAC_MAX",
        "IF NOT CONFIGURATION_VALID THEN",
        "bounded_initial := INITIAL_DAC;",
        "IF RESET OR NOT initialized_internal THEN",
        "previous_dac := bounded_initial;",
        "DAC_OUT := previous_dac;",
        "initialized_internal := TRUE;",
        "RESET_ACTIVE := RESET;",
    )

    for fragment in required_fragments:
        assert fragment in algorithm


def test_algorithm_contains_symmetric_rate_limiting_and_bounds() -> None:
    root, _ = load_limiter()
    algorithm = algorithm_text(root)

    required_fragments = (
        "bounded_input := DAC_IN;",
        "bounded_input > DAC_MAX",
        "bounded_input < DAC_MIN",
        "delta_dac := bounded_input - previous_dac;",
        "delta_dac > MAX_DELTA_DAC",
        "limited_delta := MAX_DELTA_DAC;",
        "delta_dac < -MAX_DELTA_DAC",
        "limited_delta := -MAX_DELTA_DAC;",
        "DAC_OUT := previous_dac + limited_delta;",
        "previous_dac := DAC_OUT;",
        "LIMITED := DAC_OUT <> DAC_IN;",
    )

    for fragment in required_fragments:
        assert fragment in algorithm


def test_new_limiter_uses_english_names_and_comments() -> None:
    _, xml_text = load_limiter()
    lowercase_text = xml_text.lower()

    for term in FORBIDDEN_PORTUGUESE_TERMS:
        assert re.search(
            rf"\b{re.escape(term)}\b",
            lowercase_text,
        ) is None
