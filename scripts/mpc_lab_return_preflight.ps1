[CmdletBinding()]
param(
    [switch]$Plan,
    [switch]$LocalCheck,

    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedForteSha256 =
    "DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE"

$ExpectedOpen62541Sha256 =
    "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

$ForteExe = Join-Path `
    $ProjectRoot `
    "forte\preserved-v1\runtimes\mpc-v1\forte.exe"

$Open62541Dll = Join-Path `
    $ProjectRoot `
    "forte\preserved-v1\runtimes\mpc-v1\open62541.dll"

$Guard = Join-Path `
    $ProjectRoot `
    "scripts\mpc_zero_output_deployment_guard.py"

$SystemFile = Join-Path `
    $ProjectRoot `
    "4diac\application\OPAS_Tank_System\OPAS_Tank_System.sys"

function Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 96)
    Write-Host $Title
    Write-Host ("=" * 96)
}

if (
    ($Plan.IsPresent -and $LocalCheck.IsPresent) -or
    (-not $Plan.IsPresent -and -not $LocalCheck.IsPresent)
) {
    throw "Choose exactly one mode: -Plan or -LocalCheck."
}

Set-Location $ProjectRoot

Section "MPC LAB RETURN PRE-FLIGHT"

Write-Host "PLC ACCESS BY THIS SCRIPT: NO"
Write-Host "GATEWAY ACCESS BY THIS SCRIPT: NO"
Write-Host "FORTE START BY THIS SCRIPT: NO"
Write-Host "DEPLOYMENT BY THIS SCRIPT: NO"
Write-Host "OPC UA WRITES BY THIS SCRIPT: NO"
Write-Host "REAL ACTUATION BY THIS SCRIPT: NO"

Write-Host ""
Write-Host "Protected deployment target:"
Write-Host "  FORTE_PC -> ResRealRawMPCV1"
Write-Host ""
Write-Host "Required control state:"
Write-Host "  MpcController.ENABLE_REQUEST = FALSE"
Write-Host ""
Write-Host "Initialization allowed during protected run:"
Write-Host "  MpcInitMerge.EI1 exactly once, only after guard is already active."

if ($Plan.IsPresent) {
    Write-Host ""
    Write-Host "LAB SEQUENCE"
    Write-Host "------------"
    Write-Host "1. Confirm physical stop is accessible."
    Write-Host "2. Confirm no old FORTE instance is running."
    Write-Host "3. Confirm gateway and FORTE management ports are initially free."
    Write-Host "4. Start the established Python gateway manually."
    Write-Host "5. Verify PLC OPC UA and gateway OPC UA connectivity."
    Write-Host "6. Start only the preserved MPC V1 FORTE runtime manually."
    Write-Host "7. Run the zero-output guard for a 10 s preflight with no deployment."
    Write-Host "8. If preflight passes, run the guard again for 90 s."
    Write-Host "9. After INITIAL ZERO OUTPUT: PASSED, deploy only ResRealRawMPCV1."
    Write-Host "10. Keep ENABLE_REQUEST = FALSE."
    Write-Host "11. Trigger MpcInitMerge.EI1 exactly once."
    Write-Host "12. Require continuous command/applied zero output for the full guard run."
    Write-Host "13. Save Deployment Console output and the guard CSV."
    Write-Host "14. Stop. Do not enable MPC in the same step."
    Write-Host ""
    Write-Host "PASS requires:"
    Write-Host "  Enable=False"
    Write-Host "  DAC=0"
    Write-Host "  AppliedEnable=False"
    Write-Host "  AppliedDAC=0"
    Write-Host "  WatchdogHealthy=True observed"
    Write-Host "  no UNSUPPORTED_TYPE for the MPC custom FBs"
    Write-Host "  no ZERO-OUTPUT VIOLATION"
    Write-Host ""
    Write-Host "FAIL / ABORT if:"
    Write-Host "  any actuator command/applied value becomes active/non-zero"
    Write-Host "  watchdog becomes unhealthy"
    Write-Host "  FORTE exits unexpectedly"
    Write-Host "  deployment reports unsupported custom MPC type"
    Write-Host "  the resource cannot be created cleanly"
    Write-Host ""
    Write-Host "REAL MPC AUTHORIZED: NO"
    exit 0
}

Section "LOCAL ARTIFACT CHECK"

foreach ($item in @(
    [PSCustomObject]@{ Path = $ForteExe; Label = "MPC V1 forte.exe" },
    [PSCustomObject]@{ Path = $Open62541Dll; Label = "MPC V1 open62541.dll" },
    [PSCustomObject]@{ Path = $Guard; Label = "Canonical zero-output guard" },
    [PSCustomObject]@{ Path = $SystemFile; Label = "4diac system file" }
)) {
    if (-not (Test-Path -LiteralPath $item.Path -PathType Leaf)) {
        throw "$($item.Label) not found: $($item.Path)"
    }
    Write-Host "FOUND: $($item.Label)"
}

$ForteHash = (
    Get-FileHash `
        -LiteralPath $ForteExe `
        -Algorithm SHA256
).Hash

$OpenHash = (
    Get-FileHash `
        -LiteralPath $Open62541Dll `
        -Algorithm SHA256
).Hash

Write-Host "FORTE SHA256:     $ForteHash"
Write-Host "open62541 SHA256: $OpenHash"

if ($ForteHash -ne $ExpectedForteSha256) {
    throw "Preserved MPC V1 FORTE hash mismatch."
}

if ($OpenHash -ne $ExpectedOpen62541Sha256) {
    throw "Preserved open62541.dll hash mismatch."
}

$GitStatus = @(git status --porcelain)

if ($GitStatus.Count -ne 0) {
    git status --short
    throw "Repository working tree is not clean."
}

Write-Host "Working tree clean: YES"

$RunningForte = @(
    Get-Process forte -ErrorAction SilentlyContinue
)

if ($RunningForte.Count -ne 0) {
    Write-Host ""
    Write-Host "Existing FORTE process(es):"
    $RunningForte |
        Select-Object Id,ProcessName,Path |
        Format-Table -AutoSize

    throw "FORTE must be stopped before the protected lab sequence begins."
}

foreach ($Port in 4841,61499) {
    $Listeners = @(
        Get-NetTCPConnection `
            -State Listen `
            -LocalPort $Port `
            -ErrorAction SilentlyContinue
    )

    if ($Listeners.Count -ne 0) {
        Write-Host ""
        Write-Host "Listener found on local port ${Port}:"
        $Listeners |
            Select-Object LocalAddress,LocalPort,OwningProcess |
            Format-Table -AutoSize

        throw "Local port $Port must be free at the beginning of the lab procedure."
    }

    Write-Host "Local port $Port free: YES"
}

Write-Host ""
Write-Host "LOCAL MPC LAB PRE-FLIGHT: PASSED"
Write-Host "PLC/GATEWAY CONTACT PERFORMED: NO"
Write-Host "FORTE STARTED: NO"
Write-Host "REAL MPC AUTHORIZED: NO"
Write-Host "NEXT: follow -Plan and the versioned lab runbook while physically present."