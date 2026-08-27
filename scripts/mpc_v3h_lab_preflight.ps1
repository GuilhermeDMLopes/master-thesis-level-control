[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$RuntimeDir = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($RuntimeDir)) {
    $RuntimeDir = Join-Path `
        $ProjectRoot `
        "forte\preserved-v3h-3_9\runtimes\mpc-v3h-3_9"
}

$ExpectedForteHash = "2535F31A5A5FC246BFC699ABDB4171531C71E56C4B72675D284C1322F7FAF31A"
$ExpectedOpen62541Hash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

Set-Location $ProjectRoot

Write-Host "PLC ACCESS BY THIS SCRIPT: NO"
Write-Host "GATEWAY ACCESS BY THIS SCRIPT: NO"
Write-Host "FORTE START BY THIS SCRIPT: NO"
Write-Host "DEPLOYMENT BY THIS SCRIPT: NO"
Write-Host "OPC UA WRITES BY THIS SCRIPT: NO"
Write-Host "REAL ACTUATION BY THIS SCRIPT: NO"
Write-Host ""

$ForteExe = Join-Path $RuntimeDir "forte.exe"
$Open62541 = Join-Path $RuntimeDir "open62541.dll"

foreach ($Path in @($ForteExe,$Open62541)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required V3H runtime file missing: $Path"
    }
}

$ForteHash = (Get-FileHash -LiteralPath $ForteExe -Algorithm SHA256).Hash
$OpenHash = (Get-FileHash -LiteralPath $Open62541 -Algorithm SHA256).Hash

if ($ForteHash -ne $ExpectedForteHash) {
    throw "V3H FORTE runtime hash mismatch."
}

if ($OpenHash -ne $ExpectedOpen62541Hash) {
    throw "V3H open62541 hash mismatch."
}

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "FORTE process already running."
}

if (@(
    Get-NetTCPConnection `
        -State Listen `
        -LocalPort 61499 `
        -ErrorAction SilentlyContinue
).Count -ne 0) {
    throw "Local management port 61499 is not free."
}

Write-Host "Protected deployment target:"
Write-Host "FORTE_PC -> ResRealRawMPCV3H"
Write-Host ""
Write-Host "Required initial control state:"
Write-Host "MpcController.ENABLE_REQUEST = FALSE"
Write-Host ""
Write-Host "Initialization:"
Write-Host "MpcInitMerge.EI1 exactly once on a fresh deployment,"
Write-Host "only while zero-output guard is active."
Write-Host ""
Write-Host "V3H contract:"
Write-Host "disturbance alpha = 0.10"
Write-Host "disturbance clamp = +/-100 raw/step"
Write-Host "predicted soft = 1100 raw"
Write-Host "predicted hard = 1400 raw"
Write-Host "measured hard = 1500 raw"
Write-Host "physical operator abort = 5 cm"
Write-Host ""
Write-Host "FORTE SHA256:     $ForteHash"
Write-Host "open62541 SHA256: $OpenHash"
Write-Host "Working tree clean: $(@(git status --porcelain).Count -eq 0)"
Write-Host "FORTE process running: NO"
Write-Host "Local port 61499 free: YES"
Write-Host ""
Write-Host "LOCAL MPC V3H LAB PRE-FLIGHT: PASSED"
Write-Host "REAL MPC AUTHORIZED: NO"
Write-Host "LAB NEXT: start/verify gateway, verify PLC connectivity, start exact V3H FORTE, then run zero-output guard."
