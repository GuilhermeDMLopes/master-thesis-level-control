[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$RuntimeRoot = "C:\Projetos\forte-mpc-v3e-runtime\mpc-v3e-candidate"
)

$ErrorActionPreference = "Stop"

$ExpectedForteHash = "B55B040828BAF5DAD961B04DE04DA625BC680E1FBAF0F04F595EB803D2F3B9E6"
$ExpectedOpenHash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

Set-Location $ProjectRoot

Write-Host "PLC ACCESS BY THIS SCRIPT: NO"
Write-Host "GATEWAY ACCESS BY THIS SCRIPT: NO"
Write-Host "FORTE START BY THIS SCRIPT: NO"
Write-Host "DEPLOYMENT BY THIS SCRIPT: NO"
Write-Host "OPC UA WRITES BY THIS SCRIPT: NO"
Write-Host "REAL ACTUATION BY THIS SCRIPT: NO"
Write-Host ""

$ForteExe = Join-Path $RuntimeRoot "forte.exe"
$OpenDll = Join-Path $RuntimeRoot "open62541.dll"

foreach ($Path in @($ForteExe,$OpenDll)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing V3E runtime file: $Path"
    }
}

$ForteHash = (Get-FileHash $ForteExe -Algorithm SHA256).Hash
$OpenHash = (Get-FileHash $OpenDll -Algorithm SHA256).Hash

if ($ForteHash -ne $ExpectedForteHash) {
    throw "V3E forte.exe hash mismatch."
}

if ($OpenHash -ne $ExpectedOpenHash) {
    throw "V3E open62541.dll hash mismatch."
}

$ForteRunning = @(Get-Process forte -ErrorAction SilentlyContinue).Count -gt 0
$Port61499 = @(
    Get-NetTCPConnection -State Listen -LocalPort 61499 -ErrorAction SilentlyContinue
).Count -gt 0

Write-Host "Protected deployment target:"
Write-Host "  FORTE_PC -> ResRealRawMPCV3E"
Write-Host ""
Write-Host "Required initial control state:"
Write-Host "  MpcController.ENABLE_REQUEST = FALSE"
Write-Host ""
Write-Host "Initialization:"
Write-Host "  MpcInitMerge.EI1 exactly once on a fresh deployment,"
Write-Host "  only while zero-output guard is active."
Write-Host ""
Write-Host "Expanded envelope:"
Write-Host "  predicted soft = 1100 raw"
Write-Host "  predicted hard = 1400 raw"
Write-Host "  measured hard = 1500 raw"
Write-Host "  physical operator abort = 5 cm"
Write-Host ""
Write-Host "FORTE SHA256:     $ForteHash"
Write-Host "open62541 SHA256: $OpenHash"
Write-Host "Working tree clean: $($(if (@(git status --porcelain).Count -eq 0) { 'YES' } else { 'NO' }))"
Write-Host "FORTE process running: $($(if ($ForteRunning) { 'YES' } else { 'NO' }))"
Write-Host "Local port 61499 free: $($(if (-not $Port61499) { 'YES' } else { 'NO' }))"
Write-Host ""
Write-Host "LOCAL MPC V3E LAB PRE-FLIGHT: PASSED"
Write-Host "REAL MPC AUTHORIZED: NO"
Write-Host "LAB NEXT: start gateway, verify connectivity, start V3E FORTE, then run zero-output guard."
