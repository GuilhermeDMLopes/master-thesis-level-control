from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_forte_mpc_v1.ps1"


def text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_reproduction_script_exists():
    assert SCRIPT.is_file()


def test_exact_source_revisions_are_pinned():
    source = text()
    assert "7c8b6296227fa292c13d71d2958a404c6db03e53" in source
    assert "ce5209d78d3821504d31b3bbdb03f53d6e3f93a7" in source


def test_validated_runtime_hash_is_pinned():
    assert (
        "DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE"
        in text()
    )


def test_open62541_runtime_hash_is_pinned():
    assert (
        "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"
        in text()
    )


def test_all_three_custom_fbs_are_required():
    source = text()
    for name in (
        "MPC_MEDIAN_FILTER_9",
        "MPC_MOVE_BLOCKED_NMPC_V1",
        "SAFE_DAC_RATE_LIMITER",
    ):
        assert name in source


def test_build_uses_repository_preserved_module():
    source = text()
    assert "forte\\preserved-v1" in source
    assert "external-modules\\mpc-v1" in source


def test_build_recreates_preserved_forte_source_state():
    source = text()
    assert "dirty-tracked.patch" in source
    assert "untracked-overlay" in source
    assert "worktree add" in source
    assert "apply" in source


def test_external_mpc_module_is_enabled():
    assert "-DFORTE_MODULE_EXTERNAL_MPC_V1=ON" in text()


def test_opcua_and_required_modules_are_enabled():
    source = text()
    for option in (
        "-DFORTE_COM_OPC_UA=ON",
        "-DFORTE_MODULE_CONVERT=ON",
        "-DFORTE_MODULE_IEC61131=ON",
        "-DFORTE_MODULE_UTILS=ON",
        "-DFORTE_USE_64BIT_DATATYPES=ON",
        "-DFORTE_USE_REAL_DATATYPE=ON",
        "-DFORTE_SUPPORT_MONITORING=ON",
    ):
        assert option in source


def test_no_network_download_command_is_present():
    lowered = text().lower()
    for token in (
        "invoke-webrequest",
        "start-bitstransfer",
        "curl.exe",
        "wget.exe",
        "git clone",
        "git fetch",
        "git pull",
    ):
        assert token not in lowered


def test_no_plant_or_gateway_endpoint_is_present():
    source = text()
    assert "10.0.0.3" not in source
    assert "opc.tcp://" not in source
    assert "gateway_opcua" not in source


def test_verify_only_mode_does_not_build():
    source = text()
    assert "$VerifyOnly" in source
    assert "BUILD PERFORMED: NO" in source