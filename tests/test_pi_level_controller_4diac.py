from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_PATH = (
    REPOSITORY_ROOT
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
    / "Type Library"
    / "net_custom"
    / "PI_LEVEL_CONTROLLER.fbt"
)

EXPECTED_INPUTS = {
    "PROCESS_VARIABLE": "LREAL",
    "SETPOINT": "LREAL",
    "PROPORTIONAL_GAIN": "LREAL",
    "INTEGRAL_GAIN": "LREAL",
    "SAMPLING_TIME_S": "LREAL",
    "OUTPUT_MIN": "LREAL",
    "OUTPUT_MAX": "LREAL",
    "MANUAL": "BOOL",
    "MANUAL_OUTPUT": "LREAL",
    "RESET": "BOOL",
}

EXPECTED_OUTPUTS = {
    "OUTPUT": "LREAL",
    "ERROR": "LREAL",
    "PROPORTIONAL_TERM": "LREAL",
    "INTEGRAL_TERM": "LREAL",
    "UNSATURATED_OUTPUT": "LREAL",
    "SATURATED": "BOOL",
    "MANUAL_ACTIVE": "BOOL",
    "RESET_ACTIVE": "BOOL",
    "CONFIGURATION_VALID": "BOOL",
}

FORBIDDEN_PORTUGUESE_TERMS = {
    "processo",
    "nivel",
    "saída",
    "saida",
    "erro anterior",
    "reinicialização",
    "reinicializacao",
}


def load_controller() -> tuple[ET.Element, str]:
    xml_text = CONTROLLER_PATH.read_text(encoding="utf-8")
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
        "./BasicFB/Algorithm[@Name='PI_CONTROL_ALGORITHM']/ST"
    )
    assert st_element is not None
    assert st_element.text is not None
    return st_element.text


def test_controller_file_is_well_formed_and_additive() -> None:
    root, _ = load_controller()

    assert root.attrib["Name"] == "PI_LEVEL_CONTROLLER"
    assert CONTROLLER_PATH.name == "PI_LEVEL_CONTROLLER.fbt"


def test_controller_interface_matches_the_specification() -> None:
    root, _ = load_controller()

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


def test_controller_ecc_executes_one_algorithm_and_one_confirmation() -> None:
    root, _ = load_controller()

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
        "/ECAction[@Algorithm='PI_CONTROL_ALGORITHM']"
    )
    confirm_action = root.find(
        "./BasicFB/ECC/ECState[@Name='CONFIRM']"
        "/ECAction[@Output='CNF']"
    )

    assert calculate_action is not None
    assert confirm_action is not None


def test_algorithm_contains_configuration_reset_and_manual_behavior() -> None:
    root, _ = load_controller()
    algorithm = algorithm_text(root)

    required_fragments = (
        "SAMPLING_TIME_S > 0.0",
        "OUTPUT_MIN < OUTPUT_MAX",
        "IF NOT CONFIGURATION_VALID THEN",
        "ELSIF RESET THEN",
        "ELSIF MANUAL THEN",
        "integral_term_internal := OUTPUT - PROPORTIONAL_TERM;",
        "manual_was_active := TRUE;",
    )

    for fragment in required_fragments:
        assert fragment in algorithm


def test_algorithm_contains_conditional_anti_windup() -> None:
    root, _ = load_controller()
    algorithm = algorithm_text(root)

    required_fragments = (
        "INTEGRAL_GAIN",
        "* ERROR",
        "* SAMPLING_TIME_S",
        "candidate_unsaturated_output > OUTPUT_MAX",
        "integral_increment > 0.0",
        "candidate_unsaturated_output < OUTPUT_MIN",
        "integral_increment < 0.0",
        "integral_term_internal :=\n                candidate_integral;",
    )

    for fragment in required_fragments:
        assert fragment in algorithm


def test_new_controller_uses_english_names_and_comments() -> None:
    _, xml_text = load_controller()
    lowercase_text = xml_text.lower()

    for term in FORBIDDEN_PORTUGUESE_TERMS:
        assert re.search(rf"\b{re.escape(term)}\b", lowercase_text) is None
