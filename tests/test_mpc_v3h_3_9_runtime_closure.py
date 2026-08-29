from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESERVED = ROOT / "forte" / "preserved-v3h-3_9"
MODULE = PRESERVED / "external-modules" / "MPC_V3H"
RUNTIME = PRESERVED / "runtimes" / "mpc-v3h-3_9"
EVIDENCE = (
    ROOT
    / "data"
    / "sample"
    / "mpc-v3h-3_9-runtime-smoke-20260826-213438"
)
BUILD = ROOT / "scripts" / "build_forte_mpc_v3h_3_9.ps1"
PREFLIGHT = ROOT / "scripts" / "mpc_v3h_lab_preflight.ps1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_final_runtime_artifacts_and_hashes_are_preserved():
    assert sha256(RUNTIME / "forte.exe") == "2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A"
    assert sha256(RUNTIME / "open62541.dll") == "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"
    assert (RUNTIME / "README.txt").is_file()


def test_final_exported_controller_hashes_are_preserved():
    assert sha256(MODULE / "MPC_MOVE_BLOCKED_NMPC_V3H.cpp") == "8E4416BA2EA270F23C58EF44AD9C420BEA776875F2154CE7DE8439F0D36FFF26"
    assert sha256(MODULE / "MPC_MOVE_BLOCKED_NMPC_V3H.h") == "FCD18ACA11255185800DA27BDC02CB0AC0C7127CA0884583D9FC7A2295170576"


def test_final_export_contains_corrected_v3h_soft_penalty():
    cpp = (MODULE / "MPC_MOVE_BLOCKED_NMPC_V3H.cpp").read_text(
        encoding="utf-8"
    )
    header = (MODULE / "MPC_MOVE_BLOCKED_NMPC_V3H.h").read_text(
        encoding="utf-8"
    )
    assert "st_soft_excess() = SUB(st_predicted_y(), 1100.0);" in cpp
    assert "st_soft_excess() = SUB(st_predicted_y(), 650.0);" not in cpp
    assert "3.9: 2026-08-26/Guilherme" in header


def test_final_build_script_is_pinned_and_offline():
    text = BUILD.read_text(encoding="ascii")
    for required in (
        "8E4416BA2EA270F23C58EF44AD9C420BEA776875F2154CE7DE8439F0D36FFF26",
        "FCD18ACA11255185800DA27BDC02CB0AC0C7127CA0884583D9FC7A2295170576",
        "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318",
        "FORTE_MODULE_EXTERNAL_MPC_V3H=ON",
        "forte\\preserved-v3h-3_9\\external-modules",
    ):
        assert required in text
    assert "Start-Process" not in text
    assert "opc.tcp://" not in text


def test_lab_preflight_pins_final_preserved_runtime():
    text = PREFLIGHT.read_text(encoding="utf-8-sig")
    assert "2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A" in text
    assert "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318" in text
    assert "forte\\preserved-v3h-3_9\\runtimes\\mpc-v3h-3_9" in text
    assert "Start-Process" not in text


def test_final_smoke_evidence_and_documentation_are_preserved():
    assert sha256(EVIDENCE / "forte-v3h-3_9-smoke.out.log") == "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
    assert sha256(EVIDENCE / "forte-v3h-3_9-smoke.err.log") == "537844F1C606EC573C734C296914DCEC6EA13EC992E6E6828D4206E03416F108"
    assert sha256(EVIDENCE / "smoke-summary.txt") == "CC7F42F4F0FB6337BC484FC3DCCA9A44522C5054C366D8FF9306FF16B3560639"
    doc = (
        ROOT
        / "docs"
        / "experiments"
        / "mpc-v3h-3_9-runtime-smoke-validation.md"
    ).read_text(encoding="utf-8")
    assert "OFFLINE_V3H_3_9_RUNTIME_TYPE_SMOKE_PASSED" in doc
    assert "MpcInitMerge.EI1` was not triggered" in doc
