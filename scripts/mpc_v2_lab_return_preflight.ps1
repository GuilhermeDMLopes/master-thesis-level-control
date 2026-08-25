[CmdletBinding()]
param(
    [switch]$LocalCheck
)

$ErrorActionPreference = "Stop"

$ExpectedForteHash = "49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173"
$ExpectedOpenHash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "PLC ACCESS BY THIS SCRIPT: NO"
Write-Host "GATEWAY ACCESS BY THIS SCRIPT: NO"
Write-Host "FORTE START BY THIS SCRIPT: NO"
Write-Host "DEPLOYMENT BY THIS SCRIPT: NO"
Write-Host "OPC UA WRITES BY THIS SCRIPT: NO"
Write-Host "REAL ACTUATION BY THIS SCRIPT: NO"
Write-Host ""

Write-Host "Protected deployment target:"
Write-Host "FORTE_PC -> ResRealRawMPCV2"
Write-Host ""

Write-Host "Required control state:"
Write-Host "MpcController.ENABLE_REQUEST = FALSE"
Write-Host ""

Write-Host "Initialization:"
Write-Host "MpcInitMerge.EI1 exactly once, only after zero-output guard is active."
Write-Host ""

$Runtime = Join-Path $Root "forte\preserved-v2\runtimes\mpc-v2"
$Forte = Join-Path $Runtime "forte.exe"
$Open = Join-Path $Runtime "open62541.dll"
$System = Join-Path $Root "4diac\application\OPAS_Tank_System\OPAS_Tank_System.sys"

foreach ($Check in @(
    @{Name="MPC V2 forte.exe";Path=$Forte},
    @{Name="MPC V2 open62541.dll";Path=$Open},
    @{Name="4diac system file";Path=$System},
    @{Name="canonical zero-output guard";Path=(Join-Path $Root "scripts\mpc_zero_output_deployment_guard.py")}
)) {
    if (-not (Test-Path -LiteralPath $Check.Path -PathType Leaf)) {
        throw "MISSING: $($Check.Name): $($Check.Path)"
    }

    Write-Host "FOUND: $($Check.Name)"
}

$ForteHash = (Get-FileHash -LiteralPath $Forte -Algorithm SHA256).Hash
$OpenHash = (Get-FileHash -LiteralPath $Open -Algorithm SHA256).Hash

Write-Host "FORTE SHA256:     $ForteHash"
Write-Host "open62541 SHA256: $OpenHash"

if ($ForteHash -ne $ExpectedForteHash) {
    throw "FORTE MPC V2 hash mismatch."
}

if ($OpenHash -ne $ExpectedOpenHash) {
    throw "open62541.dll hash mismatch."
}

if (@(git status --porcelain).Count -ne 0) {
    git status --short
    throw "Working tree is not clean."
}

Write-Host "Working tree clean: YES"

$ForteRunning = @(Get-Process forte -ErrorAction SilentlyContinue)
$Port61499 = @(
    Get-NetTCPConnection `
        -State Listen `
        -LocalPort 61499 `
        -ErrorAction SilentlyContinue
)

Write-Host "FORTE process running: $(
    if ($ForteRunning.Count -eq 0) { 'NO' } else { 'YES' }
)"
Write-Host "Local port 61499 free: $(
    if ($Port61499.Count -eq 0) { 'YES' } else { 'NO' }
)"

if ($ForteRunning.Count -ne 0) {
    throw "FORTE is already running."
}

if ($Port61499.Count -ne 0) {
    throw "Port 61499 is not free."
}

Write-Host ""
Write-Host "LOCAL MPC V2 LAB PRE-FLIGHT: PASSED"
Write-Host "PLC/GATEWAY CONTACT PERFORMED: NO"
Write-Host "FORTE STARTED: NO"
Write-Host "REAL MPC AUTHORIZED: NO"
Write-Host ""

if ($LocalCheck) {
    Write-Host "NEXT: wait until physically present in the laboratory."
}
else {
    Write-Host "LAB NEXT: start gateway, verify real connectivity, start preserved V2 FORTE, then run protected zero-output guard."
}
