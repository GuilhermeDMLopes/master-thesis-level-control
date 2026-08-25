from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_forte_mpc_v2.ps1"
GUIDE = ROOT / "docs" / "forte" / "forte-mpc-v2-build.md"
RUNTIME = ROOT / "forte" / "preserved-v2" / "runtimes" / "mpc-v2"


def test_build_workflow_files_exist():
    assert BUILD_SCRIPT.is_file()
    assert GUIDE.is_file()
    assert (RUNTIME / "forte.exe").is_file()
    assert (RUNTIME / "open62541.dll").is_file()
    assert (RUNTIME / "README.txt").is_file()


def test_build_script_preserves_offline_contract():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "FORTE_COM_ETH=ON" in text
    assert "FORTE_COM_FBDK=ON" in text
    assert "FORTE_COM_LOCAL=ON" in text
    assert "FORTE_COM_RAW=ON" in text
    assert "FORTE_MODULE_EXTERNAL_MPC_V2=ON" in text
    assert "FORTE_ARCHITECTURE=Win32" in text
    assert "Start-Process" not in text
    assert "opc.tcp://10.0.0.3" not in text
    assert "REAL MPC FULL OPERATION AUTHORIZED: NO" in text


def test_build_script_pins_validated_dependencies():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "77E1CE99CB7AB3A24C57EFCBBF02C5A1CF0F9C6CBCF0B1724918357B4E0764E1" in text
    assert "D2E6573E8AF6414EA01CED947BE8310BFC6047E16B27E1B961BEA4D17A73A394" in text
    assert "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318" in text


def test_guide_records_linker_fix_and_runtime_hash():
    text = GUIDE.read_text(encoding="utf-8")
    assert "CWin32SocketInterface" in text
    assert "CFDSelectHandler" in text
    assert "49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173" in text
    assert "REAL MPC FULL OPERATION AUTHORIZED: NO" in text
