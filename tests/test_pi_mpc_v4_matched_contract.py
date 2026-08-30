from pathlib import Path
import xml.etree.ElementTree as ET


SYSTEM = Path(
    "4diac/application/OPAS_Tank_System/OPAS_Tank_System.sys"
)


def root():
    return ET.parse(SYSTEM).getroot()


def named(parent, tag, name):
    matches = [item for item in parent.iter(tag) if item.get("Name") == name]
    assert len(matches) == 1
    return matches[0]


def params(fb):
    return {
        item.get("Name"): item.get("Value")
        for item in fb.findall("Parameter")
    }


def test_historical_raw_pi_is_unchanged():
    tree = root()
    app = named(tree, "Application", "PI_REAL_RAW_SAFE")
    pi = named(app, "FB", "RawPI")
    limiter = named(app, "FB", "RawSafeDACLimiter")
    assert params(pi)["SETPOINT"] == "LREAL#450.0"
    assert params(pi)["PROPORTIONAL_GAIN"] == "LREAL#4.0"
    assert params(pi)["INTEGRAL_GAIN"] == "LREAL#0.02"
    assert params(limiter)["DAC_MAX"] == "LREAL#12000.0"


def test_matched_pi_application_contract():
    tree = root()
    app = named(tree, "Application", "PI_REAL_RAW_HIGH_RANGE_COMPARE")
    pi = named(app, "FB", "RawPI")
    bias = named(app, "FB", "RawDACBias")
    limiter = named(app, "FB", "RawSafeDACLimiter")
    assert params(pi) == {
        "SETPOINT": "LREAL#17000.0",
        "PROPORTIONAL_GAIN": "LREAL#4.0",
        "INTEGRAL_GAIN": "LREAL#0.10",
        "SAMPLING_TIME_S": "LREAL#0.1",
        "OUTPUT_MIN": "LREAL#-14000.0",
        "OUTPUT_MAX": "LREAL#2000.0",
        "MANUAL": "TRUE",
        "MANUAL_OUTPUT": "LREAL#-14000.0",
        "RESET": "FALSE",
    }
    assert params(bias)["IN2"] == "LREAL#14000.0"
    assert params(limiter)["MAX_DELTA_DAC"] == "LREAL#150.0"
    assert params(limiter)["DAC_MAX"] == "LREAL#16000.0"


def test_matched_pi_resource_contract():
    tree = root()
    resource = named(tree, "Resource", "ResRealRawPICompare")
    pi = named(resource, "FB", "RawPI")
    bias = named(resource, "FB", "RawDACBias")
    limiter = named(resource, "FB", "RawSafeDACLimiter")
    assert params(pi)["SETPOINT"] == "LREAL#17000.0"
    assert params(pi)["MANUAL"] == "TRUE"
    assert params(pi)["MANUAL_OUTPUT"] == "LREAL#-14000.0"
    assert params(bias)["IN2"] == "LREAL#14000.0"
    assert params(limiter)["MAX_DELTA_DAC"] == "LREAL#150.0"
    assert params(limiter)["DAC_MAX"] == "LREAL#16000.0"


def test_matched_pi_has_complete_mapping():
    tree = root()
    mappings = [
        item for item in tree.findall("Mapping")
        if item.get("From", "").startswith(
            "PI_REAL_RAW_HIGH_RANGE_COMPARE."
        )
    ]
    assert len(mappings) == 11
    assert all(
        item.get("To", "").startswith("FORTE_PC.ResRealRawPICompare.")
        for item in mappings
    )


def test_pi_supervisor_is_bounded_and_pi_specific():
    text = Path("scripts/pi_high_range_validation.py").read_text(
        encoding="utf-8"
    )
    assert 'CONFIRMATION_TOKEN = "MATCHED_PI_READY"' in text
    assert "RawPI.MANUAL = FALSE" in text
    assert "ResRealRawPICompare" in text
    assert "default=180.0" in text
    assert "default=16000.0" in text
    assert "force_zero_outputs" in text
    assert "terminate_forte" in text
    assert "ACTIVE PI OUTPUT DETECTED" in text
    assert "MATCHED PI VALIDATION COMPLETED" in text
    assert "ACTIVE MPC OUTPUT DETECTED" not in text
    assert "HIGH-RANGE MPC V4 VALIDATION COMPLETED" not in text
