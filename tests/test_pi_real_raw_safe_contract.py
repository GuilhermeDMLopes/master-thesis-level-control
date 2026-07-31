from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = (
    REPOSITORY_ROOT
    / "4diac"
    / "application"
    / "OPAS_Tank_System"
    / "OPAS_Tank_System.sys"
)

APPLICATION_NAME = "PI_REAL_RAW_SAFE"
RESOURCE_NAME = "ResRealRawPI"

EXPECTED_FB_TYPES = {
    "RawLevelRead": "SUBSCRIBE_1",
    "RawLevelType": "LREAL2LREAL",
    "RawPVFilter": "PV_FILTER",
    "RawPI": "PI_LEVEL_CONTROLLER",
    "RawDACBias": "F_ADD",
    "RawSafeDACLimiter": "SAFE_DAC_RATE_LIMITER",
    "RawDACType": "F_LREAL_TO_INT",
    "RawDACWrite": "CLIENT_1_0",
    "RawEnableCheck": "F_GT",
    "RawEnableWrite": "CLIENT_1_0",
    "RawInitMerge": "E_MERGE",
}

EXPECTED_PARAMETERS = {
    "RawLevelRead": {
        "QI": "TRUE",
        "ID": '"opc_ua[SUBSCRIBE;opc.tcp://127.0.0.1:4841#;,2:s=Nivel]"',
    },
    "RawPVFilter": {
        "ALPHA": "LREAL#0.98",
        "RESET": "FALSE",
    },
    "RawPI": {
        "SETPOINT": "LREAL#450.0",
        "PROPORTIONAL_GAIN": "LREAL#8.0",
        "INTEGRAL_GAIN": "LREAL#0.05",
        "SAMPLING_TIME_S": "LREAL#0.1",
        "OUTPUT_MIN": "LREAL#-9000.0",
        "OUTPUT_MAX": "LREAL#3000.0",
        "MANUAL": "TRUE",
        "MANUAL_OUTPUT": "LREAL#-9000.0",
        "RESET": "FALSE",
    },
    "RawDACBias": {
        "IN2": "LREAL#9000.0",
    },
    "RawSafeDACLimiter": {
        "MAX_DELTA_DAC": "LREAL#150.0",
        "DAC_MIN": "LREAL#0.0",
        "DAC_MAX": "LREAL#12000.0",
        "INITIAL_DAC": "LREAL#0.0",
        "RESET": "FALSE",
    },
    "RawDACWrite": {
        "QI": "TRUE",
        "ID": '"opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=DAC]"',
    },
    "RawEnableCheck": {
        "IN2": "LREAL#0.0",
    },
    "RawEnableWrite": {
        "QI": "TRUE",
        "ID": '"opc_ua[WRITE;opc.tcp://127.0.0.1:4841#;,2:s=Enable]"',
    },
}

EXPECTED_EVENT_CONNECTIONS = {
    ("RawLevelRead.IND", "RawLevelType.REQ"),
    ("RawLevelType.CNF", "RawPVFilter.REQ"),
    ("RawPVFilter.CNF", "RawPI.REQ"),
    ("RawPI.CNF", "RawDACBias.REQ"),
    ("RawDACBias.CNF", "RawSafeDACLimiter.REQ"),
    ("RawSafeDACLimiter.CNF", "RawDACType.REQ"),
    ("RawDACType.CNF", "RawDACWrite.REQ"),
    ("RawDACWrite.CNF", "RawEnableCheck.REQ"),
    ("RawEnableCheck.CNF", "RawEnableWrite.REQ"),
    ("RawInitMerge.EO", "RawEnableWrite.INIT"),
    ("RawEnableWrite.INITO", "RawDACWrite.INIT"),
    ("RawDACWrite.INITO", "RawLevelRead.INIT"),
}

EXPECTED_DATA_CONNECTIONS = {
    ("RawLevelRead.RD_1", "RawLevelType.IN"),
    ("RawLevelType.OUT", "RawPVFilter.PV_IN"),
    ("RawPVFilter.PV_OUT", "RawPI.PROCESS_VARIABLE"),
    ("RawPI.OUTPUT", "RawDACBias.IN1"),
    ("RawDACBias.OUT", "RawSafeDACLimiter.DAC_IN"),
    ("RawSafeDACLimiter.DAC_OUT", "RawDACType.IN"),
    ("RawDACType.OUT", "RawDACWrite.SD_1"),
    ("RawDACBias.OUT", "RawEnableCheck.IN1"),
    ("RawEnableCheck.OUT", "RawEnableWrite.SD_1"),
}


def parse_system() -> ET.Element:
    return ET.parse(SYSTEM_PATH).getroot()


def find_unique(parent: ET.Element, tag: str, name: str) -> ET.Element:
    matches = [
        element
        for element in parent.findall(tag)
        if element.get("Name") == name
    ]

    assert len(matches) == 1
    return matches[0]


def fb_parameters(fb: ET.Element) -> dict[str, str]:
    return {
        parameter.get("Name", ""): parameter.get("Value", "")
        for parameter in fb.findall("Parameter")
    }


def network_contract(
    network: ET.Element,
) -> tuple[
    dict[str, str],
    dict[str, dict[str, str]],
    set[tuple[str, str]],
    set[tuple[str, str]],
]:
    fbs = {
        fb.get("Name", ""): fb.get("Type", "")
        for fb in network.findall("FB")
    }

    parameters = {
        fb.get("Name", ""): fb_parameters(fb)
        for fb in network.findall("FB")
    }

    event_connections = {
        (
            connection.get("Source", ""),
            connection.get("Destination", ""),
        )
        for connection in network.findall(
            "EventConnections/Connection"
        )
    }

    data_connections = {
        (
            connection.get("Source", ""),
            connection.get("Destination", ""),
        )
        for connection in network.findall(
            "DataConnections/Connection"
        )
    }

    return (
        fbs,
        parameters,
        event_connections,
        data_connections,
    )


def assert_network_contract(network: ET.Element) -> None:
    (
        fbs,
        parameters,
        event_connections,
        data_connections,
    ) = network_contract(network)

    assert fbs == EXPECTED_FB_TYPES
    assert event_connections == EXPECTED_EVENT_CONNECTIONS
    assert data_connections == EXPECTED_DATA_CONNECTIONS

    for fb_name, expected in EXPECTED_PARAMETERS.items():
        assert parameters[fb_name] == expected

    assert "F_DIV" not in set(fbs.values())
    assert "F_MUL" not in set(fbs.values())


def test_pi_real_raw_safe_is_additive() -> None:
    root = parse_system()

    application_names = {
        application.get("Name", "")
        for application in root.findall("Application")
    }

    assert {
        "OPAS_Tank_SystemApp",
        "GATEWAY_COMM_TEST",
        "PI_CONTROLLER_TEST",
        "PI_OFFLINE_CLOSED_LOOP",
        "PI_OFFLINE_SAFE_DAC_CLOSED_LOOP",
        APPLICATION_NAME,
    }.issubset(application_names)


def test_application_contract() -> None:
    root = parse_system()
    application = find_unique(
        root,
        "Application",
        APPLICATION_NAME,
    )

    network = application.find("SubAppNetwork")
    assert network is not None
    assert_network_contract(network)


def test_resource_contract_and_manual_start() -> None:
    root = parse_system()
    device = find_unique(root, "Device", "FORTE_PC")
    resource = find_unique(
        device,
        "Resource",
        RESOURCE_NAME,
    )

    network = resource.find("FBNetwork")
    assert network is not None
    assert_network_contract(network)

    automatic_start_destinations = {
        connection.get("Destination", "")
        for connection in network.findall(
            "EventConnections/Connection"
        )
        if connection.get("Source", "")
        in {"START.COLD", "START.WARM"}
    }

    assert "RawInitMerge.EI1" not in automatic_start_destinations
    assert "RawInitMerge.EI2" not in automatic_start_destinations


def test_all_application_fbs_are_mapped_once() -> None:
    root = parse_system()

    mappings = [
        mapping
        for mapping in root.findall("Mapping")
        if mapping.get("From", "").startswith(
            f"{APPLICATION_NAME}."
        )
    ]

    expected = {
        (
            f"{APPLICATION_NAME}.{fb_name}",
            f"FORTE_PC.{RESOURCE_NAME}.{fb_name}",
        )
        for fb_name in EXPECTED_FB_TYPES
    }

    actual = {
        (
            mapping.get("From", ""),
            mapping.get("To", ""),
        )
        for mapping in mappings
    }

    assert actual == expected
    assert len(mappings) == len(expected)
