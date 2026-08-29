[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$ForteSource = "C:\Users\guilh\4diac\4diac-forte",
    [string]$BuildDir = "C:\Users\guilh\4diac\4diac-forte\build-mpc-v4",
    [string]$ExternalRoot = "C:\Projetos\forte-external-modules-mpc-v4-build",
    [string]$Open62541Build = "C:\Users\guilh\4diac\open62541\build",
    [string]$RuntimeDir = "C:\Projetos\forte-mpc-v4-runtime\mpc-v4-candidate",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedBranch = "feature/final-4diac-mpc-evidence"
$ExpectedProjectHead = "3d1fa16"
$ExpectedForteCommit = "7c8b6296227fa292c13d71d2958a404c6db03e53"
$ExpectedOpenHash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

$ExpectedModuleHashes = [ordered]@{
    "CMakeLists.txt" = "7432F80FD3C4C70A1DFCEF870D01284B8034196D1B27747BDDB1BB41BDF73911"
    "MPC_MEDIAN_FILTER_9.cpp" = "C32F8F571C74335F11980B325EA06417BC65F54BA73D516636C6F371216A7048"
    "MPC_MEDIAN_FILTER_9.h" = "AC1C14795A87CCFE3794EA9D41DC868150B05B2FD703CABA240CFA0134FF83DD"
    "MPC_MOVE_BLOCKED_NMPC_V4.cpp" = "2B7FB16C6AD4080FC10A3A404400AF241B52C08249B58DD75B3C9AFDE21F901F"
    "MPC_MOVE_BLOCKED_NMPC_V4.h" = "3D645B9DFC25526FE9EA63028FDE15227B4F38153ED6B2A76CE0960D27D0A7D3"
    "SAFE_DAC_RATE_LIMITER.cpp" = "B10DA236772C0309E64CFED16AB16BA822BBF0C6D942F543EA6EA2C93E8A3C86"
    "SAFE_DAC_RATE_LIMITER.h" = "2A488E94DDBC055A91E2B549E63EEC4B94D6F4377EF76BB82BCF2DAA2528F621"
}

function Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 100)
    Write-Host $Title
    Write-Host ("=" * 100)
}

function Require-File {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label not found: $Path"
    }
}

function Require-Directory {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Label not found: $Path"
    }
}

function Require-ExactPath {
    param([string]$Actual, [string]$Expected, [string]$Label)
    $ActualFull = ([IO.Path]::GetFullPath($Actual)).TrimEnd("\")
    $ExpectedFull = ([IO.Path]::GetFullPath($Expected)).TrimEnd("\")
    if ($ActualFull -ne $ExpectedFull) {
        throw "$Label safety check failed. Expected exactly: $ExpectedFull"
    }
}

Set-Location $ProjectRoot

Section "BUILD FORTE MPC V4 HIGH-RANGE CANDIDATE"
Write-Host "NETWORK DOWNLOAD: NO"
Write-Host "PLC ACCESS: NO"
Write-Host "GATEWAY ACCESS: NO"
Write-Host "FORTE RUNTIME START: NO"
Write-Host "DEPLOYMENT: NO"
Write-Host "REAL ACTUATION: NO"

$Branch = (git branch --show-current).Trim()
$Head = (git rev-parse --short HEAD).Trim()
$Status = @(git status --porcelain)

Write-Host "Project branch: $Branch"
Write-Host "Project HEAD:   $Head"

if ($Branch -ne $ExpectedBranch) {
    throw "Unexpected project branch."
}
if ($Head -ne $ExpectedProjectHead) {
    throw "Unexpected project HEAD."
}
if ($Status.Count -ne 0) {
    throw "Project working tree must be clean."
}

$Module = Join-Path $ExternalRoot "MPC_V4"
$ControllerCpp = Join-Path $Module "MPC_MOVE_BLOCKED_NMPC_V4.cpp"
$ControllerHeader = Join-Path $Module "MPC_MOVE_BLOCKED_NMPC_V4.h"
$OpenDll = Join-Path $Open62541Build "bin\Debug\open62541.dll"

Section "VALIDATE EXPORTED MPC V4 MODULE"

Require-Directory $ForteSource "FORTE source"
Require-Directory $Module "MPC V4 external module"
Require-File (Join-Path $ForteSource "CMakeLists.txt") "FORTE CMakeLists.txt"
Require-File $OpenDll "open62541.dll"

foreach ($Entry in $ExpectedModuleHashes.GetEnumerator()) {
    $Path = Join-Path $Module $Entry.Key
    Require-File $Path "Exported V4 module file"
    $Actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    Write-Host "$($Entry.Key) SHA256: $Actual"
    if ($Actual -ne $Entry.Value) {
        throw "Exported V4 hash mismatch: $($Entry.Key)"
    }
}

$CMakeText = Get-Content -LiteralPath (Join-Path $Module "CMakeLists.txt") -Raw
if ($CMakeText -notmatch "forte_add_directory_module\(\)") {
    throw "CMakeLists.txt lacks forte_add_directory_module()."
}
if ($CMakeText -notmatch "forte_add_all_sourcefiles\(\)") {
    throw "CMakeLists.txt lacks forte_add_all_sourcefiles()."
}

$ControllerText = Get-Content -LiteralPath $ControllerCpp -Raw
$RequiredTokens = @(
    "st_APPLIED_DAC() <= 16000.0",
    "st_PV_RAW() >= 20000.0",
    "st_SP_RAW() >= 18000.0",
    "st_predicted_y() > 19500.0",
    "st_soft_excess() = SUB(st_predicted_y(), 18000.0)",
    "MUL(0.997231776304349",
    "MUL(0.00460784041233",
    "SUB(st_APPLIED_DAC(), 11750.0)"
)

foreach ($Token in $RequiredTokens) {
    if (-not $ControllerText.Contains($Token)) {
        throw "V4 controller contract token not found: $Token"
    }
}

if ($ControllerText.Contains("st_soft_excess() = SUB(st_predicted_y(), 1100.0)")) {
    throw "Old low-range V3H soft limit is present in V4 source."
}

$HeaderText = Get-Content -LiteralPath $ControllerHeader -Raw
if (-not $HeaderText.Contains("class FORTE_MPC_MOVE_BLOCKED_NMPC_V4")) {
    throw "V4 controller class not found in header."
}

Write-Host "MPC V4 EXPORTED MODULE VALIDATION: PASSED"

Section "VALIDATE LOCAL TOOLCHAIN AND SAFETY"

$ForteCommit = (git -C $ForteSource rev-parse HEAD).Trim()
$OpenHash = (Get-FileHash -LiteralPath $OpenDll -Algorithm SHA256).Hash

Write-Host "FORTE source commit: $ForteCommit"
Write-Host "open62541 SHA256:   $OpenHash"

if ($ForteCommit -ne $ExpectedForteCommit) {
    throw "Unexpected FORTE source commit."
}
if ($OpenHash -ne $ExpectedOpenHash) {
    throw "Unexpected open62541.dll hash."
}
if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "A FORTE process is running."
}
if (@(Get-NetTCPConnection -State Listen -LocalPort 61499 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "Port 61499 is already listening."
}

Write-Host "FORTE running: NO"
Write-Host "Port 61499 listening: NO"

Section "PREPARE ISOLATED BUILD"

$ExpectedBuildDir = Join-Path $ForteSource "build-mpc-v4"
$ExpectedRuntimeDir = "C:\Projetos\forte-mpc-v4-runtime\mpc-v4-candidate"

Require-ExactPath $BuildDir $ExpectedBuildDir "BuildDir"
Require-ExactPath $RuntimeDir $ExpectedRuntimeDir "RuntimeDir"

if ($Clean -and (Test-Path -LiteralPath $BuildDir)) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}
if (Test-Path -LiteralPath $RuntimeDir) {
    throw "Runtime output already exists: $RuntimeDir"
}
if (-not (Test-Path -LiteralPath $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
}

$ExternalCMake = $ExternalRoot.Replace("\", "/")
$OpenInclude = $Open62541Build.Replace("\", "/")
$OpenLibDir = (Join-Path $Open62541Build "bin\Debug").Replace("\", "/")

Section "CONFIGURE FORTE MPC V4"

$CMakeArgs = @(
    "-S", $ForteSource,
    "-B", $BuildDir,
    "-G", "Visual Studio 18 2026",
    "-A", "x64",
    "-DFORTE_ARCHITECTURE=Win32",
    "-DFORTE_BUILD_EXECUTABLE=ON",
    "-DFORTE_BUILD_SHARED_LIBRARY=ON",
    "-DFORTE_BUILD_STATIC_LIBRARY=OFF",
    "-DFORTE_BootfileLocation=forte.fboot",
    "-DFORTE_COM_ETH=ON",
    "-DFORTE_COM_FBDK=ON",
    "-DFORTE_COM_LOCAL=ON",
    "-DFORTE_COM_RAW=ON",
    "-DFORTE_COM_OPC_UA=ON",
    "-DFORTE_COM_OPC_UA_ENCRYPTION=OFF",
    "-DFORTE_COM_OPC_UA_INCLUDE_DIR=$OpenInclude",
    "-DFORTE_COM_OPC_UA_LIB=open62541.dll",
    "-DFORTE_COM_OPC_UA_LIB_DIR=$OpenLibDir",
    "-DFORTE_COM_OPC_UA_MULTICAST=OFF",
    "-DFORTE_COM_OPC_UA_CLIENT_PUB_INTERVAL=100.0",
    "-DFORTE_COM_OPC_UA_SERVER_PUB_INTERVAL=100.0",
    "-DFORTE_EXTERNAL_MODULES_DIRECTORY=$ExternalCMake",
    "-DFORTE_MODULE_EXTERNAL_MPC_V4=ON",
    "-DFORTE_MODULE_CONVERT=ON",
    "-DFORTE_MODULE_IEC61131=ON",
    "-DFORTE_MODULE_UTILS=ON",
    "-DFORTE_SUPPORT_ARRAYS=ON",
    "-DFORTE_SUPPORT_BOOT_FILE=ON",
    "-DFORTE_SUPPORT_CUSTOM_SERIALIZABLE_DATATYPES=ON",
    "-DFORTE_SUPPORT_MONITORING=ON",
    "-DFORTE_SUPPORT_QUERY_CMD=ON",
    "-DFORTE_USE_64BIT_DATATYPES=ON",
    "-DFORTE_USE_REAL_DATATYPE=ON",
    "-DFORTE_USE_WSTRING_DATATYPE=ON",
    "-DFORTE_LOGLEVEL=LOGDEBUG",
    "-DFORTE_TESTS=OFF",
    "-DFORTE_SYSTEM_TESTS=OFF"
)

$SavedErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& cmake @CMakeArgs
$CMakeConfigureExit = $LASTEXITCODE
$ErrorActionPreference = $SavedErrorActionPreference

if ($CMakeConfigureExit -ne 0) {
    throw "CMake configure failed."
}

Section "BUILD FORTE MPC V4"

$SavedErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& cmake --build $BuildDir --config Debug --parallel 8
$CMakeBuildExit = $LASTEXITCODE
$ErrorActionPreference = $SavedErrorActionPreference

if ($CMakeBuildExit -ne 0) {
    throw "FORTE MPC V4 build failed."
}

Section "VERIFY COMPILED TYPES"

foreach ($Type in @(
    "MPC_MEDIAN_FILTER_9",
    "MPC_MOVE_BLOCKED_NMPC_V4",
    "SAFE_DAC_RATE_LIMITER"
)) {
    $Objects = @(
        Get-ChildItem -LiteralPath $BuildDir -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "$Type.obj" }
    )
    $Generated = @(
        Get-ChildItem -LiteralPath $BuildDir -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "${Type}_gen.cpp" }
    )
    if ($Objects.Count -lt 1 -or $Generated.Count -lt 1) {
        throw "Compilation evidence missing for $Type."
    }
    Write-Host "COMPILED: $Type"
}

$ForteExe = Join-Path $BuildDir "src\Debug\forte.exe"
Require-File $ForteExe "FORTE V4 executable"

$ForteHash = (Get-FileHash -LiteralPath $ForteExe -Algorithm SHA256).Hash
Write-Host "FORTE V4 SHA256: $ForteHash"

Section "PREPARE ISOLATED V4 RUNTIME"

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
Copy-Item -LiteralPath $ForteExe -Destination (Join-Path $RuntimeDir "forte.exe")
Copy-Item -LiteralPath $OpenDll -Destination (Join-Path $RuntimeDir "open62541.dll")

$Readme = @"
FORTE MPC V4 high-range candidate runtime

Generated from project commit:
$ExpectedProjectHead

FORTE source commit:
$ExpectedForteCommit

FORTE SHA256:
$ForteHash

open62541 SHA256:
$ExpectedOpenHash

MPC controller source SHA256:
$($ExpectedModuleHashes["MPC_MOVE_BLOCKED_NMPC_V4.cpp"])

The build script did not start FORTE, access the PLC/gateway, deploy an application, or authorize real actuation.
"@

[IO.File]::WriteAllText(
    (Join-Path $RuntimeDir "README.txt"),
    $Readme.Replace("`r`n", "`n").TrimEnd() + "`n",
    [Text.UTF8Encoding]::new($false)
)

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "FORTE unexpectedly running after build."
}
if (@(Get-NetTCPConnection -State Listen -LocalPort 61499 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "Port 61499 unexpectedly listening after build."
}

Write-Host ""
Write-Host "M5F_MPC_V4_BUILD_PASSED"
Write-Host "Runtime: $RuntimeDir"
Write-Host "FORTE SHA256: $ForteHash"
Write-Host "open62541 SHA256: $OpenHash"
Write-Host "FORTE STARTED: NO"
Write-Host "DEPLOYMENT PERFORMED: NO"
Write-Host "PLC/GATEWAY ACCESSED: NO"
Write-Host "REAL ACTUATION AUTHORIZED: NO"
