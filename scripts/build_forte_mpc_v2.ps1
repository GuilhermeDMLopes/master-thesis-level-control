[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$ForteSource = "C:\Users\guilh\4diac\4diac-forte",
    [string]$BuildDir = "C:\Users\guilh\4diac\4diac-forte\build-mpc-v2",
    [string]$ExternalRoot = "C:\Projetos\forte-external-modules-mpc-v2-build",
    [string]$ExportRoot = "C:\Projetos\forte-external-modules-mpc-v2\EXPORT_MPC_V2",
    [string]$Open62541Build = "C:\Users\guilh\4diac\open62541\build",
    [string]$RuntimeDir = "C:\Projetos\forte-mpc-v2-validation",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedCppHash = "77E1CE99CB7AB3A24C57EFCBBF02C5A1CF0F9C6CBCF0B1724918357B4E0764E1"
$ExpectedHeaderHash = "D2E6573E8AF6414EA01CED947BE8310BFC6047E16B27E1B961BEA4D17A73A394"
$ExpectedOpenHash = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

function Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 100)
    Write-Host $Title
    Write-Host ("=" * 100)
}

Set-Location $ProjectRoot

Section "BUILD FORTE MPC V2"

Write-Host "PLC ACCESS: NO"
Write-Host "GATEWAY ACCESS: NO"
Write-Host "FORTE RUNTIME START: NO"
Write-Host "DEPLOYMENT: NO"
Write-Host "REAL ACTUATION: NO"

$Module = Join-Path $ExternalRoot "MPC_V2"
$Cpp = Join-Path $Module "MPC_MOVE_BLOCKED_NMPC_V2.cpp"
$Header = Join-Path $Module "MPC_MOVE_BLOCKED_NMPC_V2.h"
$ExportCpp = Join-Path $ExportRoot "MPC_MOVE_BLOCKED_NMPC_V2.cpp"
$ExportHeader = Join-Path $ExportRoot "MPC_MOVE_BLOCKED_NMPC_V2.h"
$OpenDll = Join-Path $Open62541Build "bin\Debug\open62541.dll"

Section "VALIDATE INPUTS"

foreach ($Path in @(
    (Join-Path $ForteSource "CMakeLists.txt"),
    (Join-Path $Module "CMakeLists.txt"),
    $Cpp,
    $Header,
    $ExportCpp,
    $ExportHeader,
    $OpenDll
)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required input missing: $Path"
    }
}

$HashChecks = @(
    @{Path=$Cpp; Expected=$ExpectedCppHash; Name="module CPP"},
    @{Path=$ExportCpp; Expected=$ExpectedCppHash; Name="export CPP"},
    @{Path=$Header; Expected=$ExpectedHeaderHash; Name="module header"},
    @{Path=$ExportHeader; Expected=$ExpectedHeaderHash; Name="export header"},
    @{Path=$OpenDll; Expected=$ExpectedOpenHash; Name="open62541.dll"}
)

foreach ($Check in $HashChecks) {
    $Actual = (Get-FileHash -LiteralPath $Check.Path -Algorithm SHA256).Hash
    Write-Host "$($Check.Name): $Actual"
    if ($Actual -ne $Check.Expected) {
        throw "$($Check.Name) hash mismatch."
    }
}

$CMakeText = Get-Content -LiteralPath (Join-Path $Module "CMakeLists.txt") -Raw
if ($CMakeText -notmatch "forte_add_directory_module\(\)") {
    throw "External module CMakeLists lacks forte_add_directory_module()."
}
if ($CMakeText -notmatch "forte_add_all_sourcefiles\(\)") {
    throw "External module CMakeLists lacks forte_add_all_sourcefiles()."
}

$ForteCommit = (git -C $ForteSource rev-parse HEAD).Trim()
Write-Host "FORTE source commit: $ForteCommit"

Section "SAFETY"

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "A FORTE process is running."
}
if (@(Get-NetTCPConnection -State Listen -LocalPort 61499 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "Port 61499 is already listening."
}

Write-Host "FORTE running: NO"
Write-Host "Port 61499 listening: NO"

Section "PREPARE BUILD"

$ExpectedBuild = ([IO.Path]::GetFullPath((Join-Path $ForteSource "build-mpc-v2"))).TrimEnd("\")
$ActualBuild = ([IO.Path]::GetFullPath($BuildDir)).TrimEnd("\")

if ($ActualBuild -ne $ExpectedBuild) {
    throw "BuildDir safety check failed. Expected exactly $ExpectedBuild"
}

if ($Clean -and (Test-Path -LiteralPath $BuildDir)) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
}

$ExternalCMake = $ExternalRoot.Replace("\","/")
$OpenInclude = $Open62541Build.Replace("\","/")
$OpenLibDir = (Join-Path $Open62541Build "bin\Debug").Replace("\","/")

Section "CONFIGURE"

$Args = @(
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
    "-DFORTE_MODULE_EXTERNAL_MPC_V2=ON",
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

& cmake @Args
if ($LASTEXITCODE -ne 0) {
    throw "CMake configure failed."
}

Section "BUILD"

& cmake --build $BuildDir --config Debug --parallel 8
if ($LASTEXITCODE -ne 0) {
    throw "FORTE MPC V2 build failed."
}

Section "VERIFY OUTPUTS"

foreach ($Type in @(
    "MPC_MEDIAN_FILTER_9",
    "MPC_MOVE_BLOCKED_NMPC_V2",
    "SAFE_DAC_RATE_LIMITER"
)) {
    $Obj = @(
        Get-ChildItem -LiteralPath $BuildDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq "$Type.obj" }
    )
    $Gen = @(
        Get-ChildItem -LiteralPath $BuildDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq "${Type}_gen.cpp" }
    )
    if ($Obj.Count -lt 1 -or $Gen.Count -lt 1) {
        throw "Compilation evidence missing for $Type."
    }
    Write-Host "COMPILED: $Type"
}

$ForteExe = Join-Path $BuildDir "src\Debug\forte.exe"
if (-not (Test-Path -LiteralPath $ForteExe -PathType Leaf)) {
    throw "forte.exe not found."
}

$ForteHash = (Get-FileHash -LiteralPath $ForteExe -Algorithm SHA256).Hash
Write-Host "FORTE SHA256: $ForteHash"

Section "PREPARE RUNTIME"

if (Test-Path -LiteralPath $RuntimeDir) {
    Remove-Item -LiteralPath $RuntimeDir -Recurse -Force
}
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

Copy-Item -LiteralPath $ForteExe -Destination (Join-Path $RuntimeDir "forte.exe")
Copy-Item -LiteralPath $OpenDll -Destination (Join-Path $RuntimeDir "open62541.dll")

$Readme = @"
FORTE MPC V2 runtime generated by scripts/build_forte_mpc_v2.ps1

FORTE SHA256:
$ForteHash

open62541 SHA256:
$ExpectedOpenHash

Runtime not started by this build script.
Real MPC operation is not authorized by a successful build.
"@

[IO.File]::WriteAllText(
    (Join-Path $RuntimeDir "README.txt"),
    $Readme.Replace("`r`n","`n").TrimEnd() + "`n",
    [Text.UTF8Encoding]::new($false)
)

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "FORTE unexpectedly running after build."
}

Write-Host ""
Write-Host "BUILD FORTE MPC V2: PASSED"
Write-Host "FORTE V2 STARTED: NO"
Write-Host "PLC/GATEWAY ACCESSED: NO"
Write-Host "DEPLOYMENT PERFORMED: NO"
Write-Host "REAL MPC FULL OPERATION AUTHORIZED: NO"
