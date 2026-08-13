from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RUNBOOK = (
    ROOT
    / "docs"
    / "experiments"
    / "mpc-protected-zero-output-lab-runbook-v1.md"
)

PREFLIGHT = ROOT / "scripts" / "mpc_lab_return_preflight.ps1"


def runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def preflight_text() -> str:
    return PREFLIGHT.read_text(encoding="utf-8")


def test_runbook_and_preflight_exist():
    assert RUNBOOK.is_file()
    assert PREFLIGHT.is_file()


def test_canonical_runtime_hash_is_frozen():
    expected = (
        "DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE"
    )

    assert expected in runbook_text()
    assert expected in preflight_text()


def test_open62541_hash_is_frozen():
    expected = (
        "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"
    )

    assert expected in runbook_text()
    assert expected in preflight_text()


def test_runbook_requires_guard_before_deployment():
    text = runbook_text()

    guard_pos = text.index("Start the protected 90 s observation")
    deploy_pos = text.index("Deploy only the MPC resource")

    assert guard_pos < deploy_pos
    assert "INITIAL ZERO OUTPUT: PASSED" in text


def test_runbook_requires_only_mpc_resource_deployment():
    text = runbook_text()

    assert "FORTE_PC -> ResRealRawMPCV1" in text
    assert "Do not deploy the complete System or the complete device." in text


def test_runbook_never_authorizes_mpc_enable():
    text = runbook_text()

    assert "ENABLE_REQUEST = FALSE" in text
    assert "do not set `ENABLE_REQUEST = TRUE`" in text
    assert "REAL MPC AUTHORIZED: **NO**" in text


def test_runbook_requires_single_initialization_trigger():
    text = runbook_text()

    assert "`MpcInitMerge.EI1`" in text
    assert "exactly once" in text


def test_runbook_requires_all_zero_output_acceptance_signals():
    text = runbook_text()

    for required in (
        "Enable = FALSE",
        "DAC = 0",
        "AppliedEnable = FALSE",
        "AppliedDAC = 0",
        "WatchdogHealthy",
        "ZERO-OUTPUT VIOLATION",
    ):
        assert required in text


def test_runbook_checks_all_three_custom_types():
    text = runbook_text()

    for name in (
        "MPC_MEDIAN_FILTER_9",
        "MPC_MOVE_BLOCKED_NMPC_V1",
        "SAFE_DAC_RATE_LIMITER",
    ):
        assert name in text


def test_preflight_contains_no_remote_endpoint():
    text = preflight_text()

    assert "10.0.0.3" not in text
    assert "opc.tcp://" not in text


def test_preflight_does_not_start_runtime_or_gateway():
    text = preflight_text().lower()

    forbidden = (
        "start-process",
        "gateway_opcua.py",
        "write_value",
        "write_attribute",
    )

    for token in forbidden:
        assert token not in text


def test_preflight_requires_initial_local_ports_free():
    text = preflight_text()

    assert "4841,61499" in text
    assert "must be free" in text


def test_plan_explicitly_stops_before_active_mpc():
    text = preflight_text()

    assert "Do not enable MPC in the same step." in text
    assert "REAL MPC AUTHORIZED: NO" in text