[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$ForteSource = "C:\Users\guilh\4diac\4diac-forte",
    [string]$BuildDir = "C:\Users\guilh\4diac\4diac-forte\build-mpc-v3h-3_9",
    [string]$ExternalRoot = "",
    [string]$Open62541Build = "C:\Users\guilh\4diac\open62541\build",
    [string]$RuntimeDir = "C:\Projetos\forte-mpc-v3h-runtime\mpc-v3h-3_9-rebuild",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedForteCommit = "7c8b6296227fa292c13d71d2958a404c6db03e53"
$ExpectedCppHash = "8E4416BA2EA270F23C58EF44AD9C420BEA776875F2154CE7DE8439F0D36FFF26"
$ExpectedHeaderHash = "FCD18ACA11255185800DA27BDC02CB0AC0C7127CA0884583D9FC7A2295170576"
$ExpectedOpenHash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

function Section {
    param([string]$Title)

    Write-Host ""
    Write-Host ("=" * 100)
    Write-Host $Title
    Write-Host ("=" * 100)
}

function Require-File {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label not found: $Path"
    }
}

function Require-Directory {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Label not found: $Path"
    }
}

function Assert-ExactPath {
    param(
        [string]$Actual,
        [string]$Expected,
        [string]$Label
    )

    $actualFull = ([IO.Path]::GetFullPath($Actual)).TrimEnd("\")
    $expectedFull = ([IO.Path]::GetFullPath($Expected)).TrimEnd("\")

    if ($actualFull -ne $expectedFull) {
        throw "$Label safety check failed. Expected exactly $expectedFull"
    }
}

Section "BUILD FORTE MPC V3H 3.9 CANDIDATE"

Write-Host "NETWORK DOWNLOAD: NO"
Write-Host "PLC ACCESS: NO"
Write-Host "GATEWAY ACCESS: NO"
Write-Host "FORTE RUNTIME START: NO"
Write-Host "DEPLOYMENT: NO"
Write-Host "REAL ACTUATION: NO"

if ([string]::IsNullOrWhiteSpace($ExternalRoot)) {
    $ExternalRoot = Join-Path `
        $ProjectRoot `
        "forte\preserved-v3h-3_9\external-modules"
}

Require-Directory $ProjectRoot "Project repository"
Require-Directory $ForteSource "FORTE source"
Require-Directory $ExternalRoot "V3H 3.9 external module root"
Require-Directory $Open62541Build "open62541 build"

Set-Location -LiteralPath $ProjectRoot

Section "VALIDATE V3H 3.9 MODULE"

$module = Join-Path $ExternalRoot "MPC_V3H"
$cmakeFile = Join-Path $module "CMakeLists.txt"
$cpp = Join-Path $module "MPC_MOVE_BLOCKED_NMPC_V3H.cpp"
$header = Join-Path $module "MPC_MOVE_BLOCKED_NMPC_V3H.h"
$openDll = Join-Path $Open62541Build "bin\Debug\open62541.dll"

$requiredModuleFiles = @(
    "CMakeLists.txt",
    "MPC_MEDIAN_FILTER_9.cpp",
    "MPC_MEDIAN_FILTER_9.h",
    "MPC_MOVE_BLOCKED_NMPC_V3H.cpp",
    "MPC_MOVE_BLOCKED_NMPC_V3H.h",
    "SAFE_DAC_RATE_LIMITER.cpp",
    "SAFE_DAC_RATE_LIMITER.h"
)

foreach ($name in $requiredModuleFiles) {
    $path = Join-Path $module $name
    Require-File $path "External module file"
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    Write-Host "$name SHA256: $hash"
}

Require-File $openDll "open62541.dll"

$cppHash = (Get-FileHash -LiteralPath $cpp -Algorithm SHA256).Hash
$headerHash = (Get-FileHash -LiteralPath $header -Algorithm SHA256).Hash
$openHash = (Get-FileHash -LiteralPath $openDll -Algorithm SHA256).Hash

if ($cppHash -ne $ExpectedCppHash) {
    throw "V3H 3.9 CPP hash mismatch."
}

if ($headerHash -ne $ExpectedHeaderHash) {
    throw "V3H 3.9 header hash mismatch."
}

if ($openHash -ne $ExpectedOpenHash) {
    throw "open62541.dll hash mismatch."
}

$cppText = [IO.File]::ReadAllText($cpp)
$headerText = [IO.File]::ReadAllText($header)
$cmakeText = [IO.File]::ReadAllText($cmakeFile)

if (
    -not $cppText.Contains(
        "st_soft_excess() = SUB(st_predicted_y(), 1100.0);"
    )
) {
    throw "V3H 3.9 corrected soft excess was not exported."
}

if (
    $cppText.Contains(
        "st_soft_excess() = SUB(st_predicted_y(), 650.0);"
    )
) {
    throw "Historical V3H 3.8 soft excess remains in exported source."
}

if (-not $headerText.Contains("3.9: 2026-08-26/Guilherme")) {
    throw "V3H 3.9 version record missing from exported header."
}

if (-not $cmakeText.Contains("forte_add_directory_module()")) {
    throw "External module CMakeLists lacks forte_add_directory_module()."
}

if (-not $cmakeText.Contains("forte_add_all_sourcefiles()")) {
    throw "External module CMakeLists lacks forte_add_all_sourcefiles()."
}

Write-Host "V3H 3.9 MODULE VALIDATION: PASSED"

Section "VALIDATE LOCAL TOOLCHAIN AND SAFETY"

$actualForteCommit = (& git -C $ForteSource rev-parse HEAD).Trim()
Write-Host "FORTE source commit: $actualForteCommit"

if ($actualForteCommit -ne $ExpectedForteCommit) {
    throw "Unexpected FORTE source commit."
}

if (-not (Get-Command cmake.exe -ErrorAction SilentlyContinue)) {
    throw "cmake.exe is not available on PATH."
}

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "A FORTE process is already running."
}

if (@(
    Get-NetTCPConnection `
        -State Listen `
        -LocalPort 61499 `
        -ErrorAction SilentlyContinue
).Count -ne 0) {
    throw "Local management port 61499 is not free."
}

Write-Host "FORTE running: NO"
Write-Host "Port 61499 listening: NO"

Section "PREPARE ISOLATED BUILD"

$expectedBuild = "C:\Users\guilh\4diac\4diac-forte\build-mpc-v3h-3_9"
$expectedRuntime = "C:\Projetos\forte-mpc-v3h-runtime\mpc-v3h-3_9-rebuild"

Assert-ExactPath $BuildDir $expectedBuild "BuildDir"
Assert-ExactPath $RuntimeDir $expectedRuntime "RuntimeDir"

if ($Clean -and (Test-Path -LiteralPath $BuildDir)) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

if ($Clean -and (Test-Path -LiteralPath $RuntimeDir)) {
    Remove-Item -LiteralPath $RuntimeDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
}

if (Test-Path -LiteralPath $RuntimeDir) {
    throw "RuntimeDir already exists. Use -Clean only for this exact 3.9 candidate."
}

$externalCmake = $ExternalRoot.Replace("\", "/")
$openInclude = $Open62541Build.Replace("\", "/")
$openLibDir = (Join-Path $Open62541Build "bin\Debug").Replace("\", "/")

Section "CONFIGURE FORTE V3H 3.9"

$cmakeArgs = @(
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
    "-DFORTE_COM_OPC_UA_INCLUDE_DIR=$openInclude",
    "-DFORTE_COM_OPC_UA_LIB=open62541.dll",
    "-DFORTE_COM_OPC_UA_LIB_DIR=$openLibDir",
    "-DFORTE_COM_OPC_UA_MULTICAST=OFF",
    "-DFORTE_COM_OPC_UA_CLIENT_PUB_INTERVAL=100.0",
    "-DFORTE_COM_OPC_UA_SERVER_PUB_INTERVAL=100.0",
    "-DFORTE_EXTERNAL_MODULES_DIRECTORY=$externalCmake",
    "-DFORTE_MODULE_EXTERNAL_MPC_V3H=ON",
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

& cmake @cmakeArgs
if ($LASTEXITCODE -ne 0) {
    throw "CMake configure failed."
}

Section "BUILD FORTE V3H 3.9"

& cmake --build $BuildDir --config Debug --parallel 8
if ($LASTEXITCODE -ne 0) {
    throw "FORTE V3H 3.9 build failed."
}

Section "VERIFY COMPILED TYPES"

foreach ($type in @(
    "MPC_MEDIAN_FILTER_9",
    "MPC_MOVE_BLOCKED_NMPC_V3H",
    "SAFE_DAC_RATE_LIMITER"
)) {
    $objects = @(
        Get-ChildItem `
            -LiteralPath $BuildDir `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "$type.obj" }
    )

    $generatedSources = @(
        Get-ChildItem `
            -LiteralPath $BuildDir `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "${type}_gen.cpp" }
    )

    if ($objects.Count -lt 1 -or $generatedSources.Count -lt 1) {
        throw "Compilation evidence missing for $type."
    }

    Write-Host "COMPILED: $type"
}

$forteExe = Join-Path $BuildDir "src\Debug\forte.exe"
Require-File $forteExe "Built FORTE executable"

$forteHash = (Get-FileHash -LiteralPath $forteExe -Algorithm SHA256).Hash
Write-Host "FORTE V3H 3.9 SHA256: $forteHash"

Section "PREPARE ISOLATED RUNTIME"

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

Copy-Item `
    -LiteralPath $forteExe `
    -Destination (Join-Path $RuntimeDir "forte.exe")

Copy-Item `
    -LiteralPath $openDll `
    -Destination (Join-Path $RuntimeDir "open62541.dll")

$readme = @"
FORTE MPC V3H 3.9 candidate runtime

Controller CPP SHA256:
$ExpectedCppHash

Controller header SHA256:
$ExpectedHeaderHash

FORTE SHA256:
$forteHash

open62541 SHA256:
$ExpectedOpenHash

Runtime was not started by this build script.
No deployment, gateway access, PLC access, or real actuation was performed.
"@

[IO.File]::WriteAllText(
    (Join-Path $RuntimeDir "README.txt"),
    $readme.Replace("`r`n", "`n").TrimEnd() + "`n",
    (New-Object Text.UTF8Encoding($false))
)

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "FORTE unexpectedly started during build."
}

if (@(
    Get-NetTCPConnection `
        -State Listen `
        -LocalPort 61499 `
        -ErrorAction SilentlyContinue
).Count -ne 0) {
    throw "Port 61499 unexpectedly opened during build."
}

Write-Host ""
Write-Host "M5C_V3H_3_9_BUILD_PASSED"
Write-Host "Runtime: $RuntimeDir"
Write-Host "FORTE SHA256: $forteHash"
Write-Host "open62541 SHA256: $ExpectedOpenHash"
Write-Host "FORTE STARTED: NO"
Write-Host "DEPLOYMENT PERFORMED: NO"
Write-Host "PLC/GATEWAY ACCESSED: NO"
Write-Host "REAL ACTUATION AUTHORIZED: NO"
