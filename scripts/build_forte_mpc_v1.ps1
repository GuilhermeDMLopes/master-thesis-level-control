[CmdletBinding()]
param(
    [switch]$VerifyOnly,
    [switch]$Build,
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control",
    [string]$ForteSource = "C:\Users\guilh\4diac\4diac-forte",
    [string]$Open62541Source = "C:\Users\guilh\4diac\open62541",
    [string]$Open62541Build = "C:\Users\guilh\4diac\open62541\build",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedForteCommit = "7c8b6296227fa292c13d71d2958a404c6db03e53"
$ExpectedOpen62541Commit = "ce5209d78d3821504d31b3bbdb03f53d6e3f93a7"
$ExpectedRuntimeSha256 = "DBA3C8280819F648B0F75CF4F748799C7EE1CBEC5E901C2E3788302C09FB28DE"
$ExpectedOpen62541DllSha256 = "452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318"

$PreservedRoot = Join-Path $ProjectRoot "forte\preserved-v1"
$CanonicalRuntime = Join-Path $PreservedRoot "runtimes\mpc-v1\forte.exe"
$CanonicalOpen62541Dll = Join-Path $PreservedRoot "runtimes\mpc-v1\open62541.dll"
$ModuleSource = Join-Path $PreservedRoot "external-modules\mpc-v1"
$TrackedPatch = Join-Path $PreservedRoot "provenance\forte-source\dirty-tracked.patch"
$OverlayRoot = Join-Path $PreservedRoot "provenance\forte-source\untracked-overlay"

function Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 100)
    Write-Host $Title
    Write-Host ("=" * 100)
}

function Require-File {
    param([string]$Path,[string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label not found: $Path"
    }
}

function Require-Directory {
    param([string]$Path,[string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Label not found: $Path"
    }
}

if (($VerifyOnly -and $Build) -or (-not $VerifyOnly -and -not $Build)) {
    throw "Choose exactly one mode: -VerifyOnly or -Build."
}

Section "FORTE MPC V1 REPRODUCTION"
Write-Host "NETWORK DOWNLOAD: NO"
Write-Host "PLC ACCESS: NO"
Write-Host "GATEWAY ACCESS: NO"
Write-Host "FORTE DEPLOYMENT: NO"
Write-Host "REAL ACTUATION: NO"

Section "VERIFY PRESERVED MPC V1 ARTIFACTS"

Require-File $CanonicalRuntime "Canonical MPC FORTE runtime"
Require-File $CanonicalOpen62541Dll "Canonical open62541 DLL"
Require-File $TrackedPatch "Preserved FORTE tracked patch"
Require-Directory $OverlayRoot "Preserved FORTE source overlay"
Require-Directory $ModuleSource "Preserved MPC external module"

$RuntimeHash = (Get-FileHash -LiteralPath $CanonicalRuntime -Algorithm SHA256).Hash
$OpenDllHash = (Get-FileHash -LiteralPath $CanonicalOpen62541Dll -Algorithm SHA256).Hash

Write-Host "Canonical FORTE SHA256:     $RuntimeHash"
Write-Host "Canonical open62541 SHA256: $OpenDllHash"

if ($RuntimeHash -ne $ExpectedRuntimeSha256) {
    throw "Canonical MPC FORTE runtime hash mismatch."
}
if ($OpenDllHash -ne $ExpectedOpen62541DllSha256) {
    throw "Canonical open62541.dll hash mismatch."
}

$RequiredModuleFiles = @(
    "CMakeLists.txt",
    "MPC_MEDIAN_FILTER_9.cpp",
    "MPC_MEDIAN_FILTER_9.h",
    "MPC_MOVE_BLOCKED_NMPC_V1.cpp",
    "MPC_MOVE_BLOCKED_NMPC_V1.h",
    "SAFE_DAC_RATE_LIMITER.cpp",
    "SAFE_DAC_RATE_LIMITER.h"
)

foreach ($Name in $RequiredModuleFiles) {
    Require-File (Join-Path $ModuleSource $Name) "Preserved MPC module file"
    Write-Host "FOUND: $Name"
}

Write-Host "PRESERVED MPC V1 ARTIFACT VERIFICATION: PASSED"

if ($VerifyOnly) {
    Write-Host ""
    Write-Host "VERIFY-ONLY RESULT"
    Write-Host "CANONICAL MPC RUNTIME VERIFIED: YES"
    Write-Host "CANONICAL OPEN62541 DLL VERIFIED: YES"
    Write-Host "MPC EXTERNAL MODULE VERIFIED: YES"
    Write-Host "BUILD PERFORMED: NO"
    Write-Host "REAL MPC AUTHORIZED: NO"
    exit 0
}

Section "VERIFY LOCAL SOURCE PROVENANCE"

Require-Directory $ForteSource "Local FORTE source repository"
Require-Directory $Open62541Source "Local open62541 source repository"
Require-Directory $Open62541Build "Local open62541 build"

$ActualForteCommit = (git -C $ForteSource rev-parse HEAD).Trim()
$ActualOpenCommit = (git -C $Open62541Source rev-parse HEAD).Trim()

Write-Host "FORTE commit:     $ActualForteCommit"
Write-Host "open62541 commit: $ActualOpenCommit"

if ($ActualForteCommit -ne $ExpectedForteCommit) {
    throw "Unexpected FORTE source commit."
}
if ($ActualOpenCommit -ne $ExpectedOpen62541Commit) {
    throw "Unexpected open62541 source commit."
}

$OpenStatus = @(git -C $Open62541Source status --porcelain)
if ($OpenStatus.Count -ne 0) {
    throw "open62541 source tree must remain clean."
}

$LocalOpenDll = Join-Path $Open62541Build "bin\Debug\open62541.dll"
Require-File $LocalOpenDll "Local open62541.dll"

$LocalOpenDllHash = (Get-FileHash -LiteralPath $LocalOpenDll -Algorithm SHA256).Hash
Write-Host "Local open62541.dll SHA256: $LocalOpenDllHash"

if ($LocalOpenDllHash -ne $ExpectedOpen62541DllSha256) {
    throw "Local open62541.dll differs from validated dependency."
}

Section "PREPARE ISOLATED REPRODUCTION"

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $Parent = Split-Path -Parent $ProjectRoot
    $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputRoot = Join-Path $Parent "forte-reproduction-mpc-v1\$Stamp"
}

if (Test-Path -LiteralPath $OutputRoot) {
    throw "Output directory already exists: $OutputRoot"
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Worktree = Join-Path $OutputRoot "forte-source"
$ExternalRoot = Join-Path $OutputRoot "external-modules"
$ExternalModule = Join-Path $ExternalRoot "MPC_V1"
$BuildDir = Join-Path $OutputRoot "build"
$RuntimeDir = Join-Path $OutputRoot "runtime"

New-Item -ItemType Directory -Path $ExternalModule -Force | Out-Null
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

$WorktreeAdded = $false

try {
    Section "RECREATE FORTE SOURCE STATE"

    git -C $ForteSource worktree add --detach $Worktree $ExpectedForteCommit
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create detached FORTE worktree."
    }

    $WorktreeAdded = $true
    Write-Host "Clean FORTE worktree created."

    git -C $Worktree apply --whitespace=nowarn $TrackedPatch
    if ($LASTEXITCODE -ne 0) {
        throw "Could not apply preserved tracked FORTE patch."
    }

    Write-Host "Tracked FORTE patch applied."

    foreach ($Item in @(Get-ChildItem -LiteralPath $OverlayRoot -Force)) {
        Copy-Item `
            -LiteralPath $Item.FullName `
            -Destination $Worktree `
            -Recurse `
            -Force
    }

    Write-Host "Untracked FORTE source overlay restored."

    Section "RESTORE MPC EXTERNAL MODULE"

    foreach ($Name in $RequiredModuleFiles) {
        Copy-Item `
            -LiteralPath (Join-Path $ModuleSource $Name) `
            -Destination (Join-Path $ExternalModule $Name)
    }

    Get-ChildItem -LiteralPath $ExternalModule -File |
        Sort-Object Name |
        Select-Object Name,Length |
        Format-Table -AutoSize

    Section "CONFIGURE FORTE MPC V1"

    $Open62541Include = $Open62541Build.Replace("\","/")
    $Open62541LibDir = (Join-Path $Open62541Build "bin\Debug").Replace("\","/")
    $ExternalRootCmake = $ExternalRoot.Replace("\","/")

    $CmakeArgs = @(
        "-S", $Worktree,
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
        "-DFORTE_COM_OPC_UA_INCLUDE_DIR=$Open62541Include",
        "-DFORTE_COM_OPC_UA_LIB=open62541.dll",
        "-DFORTE_COM_OPC_UA_LIB_DIR=$Open62541LibDir",
        "-DFORTE_EXTERNAL_MODULES_DIRECTORY=$ExternalRootCmake",
        "-DFORTE_MODULE_EXTERNAL_MPC_V1=ON",
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

    & cmake @CmakeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "CMake configure failed."
    }

    Section "BUILD FORTE MPC V1"

    & cmake --build $BuildDir --config Debug --parallel 8
    if ($LASTEXITCODE -ne 0) {
        throw "FORTE MPC V1 build failed."
    }

    Section "VERIFY CUSTOM FB COMPILATION"

    $CustomFBs = @(
        "MPC_MEDIAN_FILTER_9",
        "MPC_MOVE_BLOCKED_NMPC_V1",
        "SAFE_DAC_RATE_LIMITER"
    )

    foreach ($Stem in $CustomFBs) {
        $Obj = @(
            Get-ChildItem `
                -LiteralPath $BuildDir `
                -Recurse `
                -File `
                -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "$Stem.obj" }
        )

        if ($Obj.Count -lt 1) {
            throw "Missing compiled object: $Stem.obj"
        }

        $Generated = @(
            Get-ChildItem `
                -LiteralPath $BuildDir `
                -Recurse `
                -File `
                -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "${Stem}_gen.cpp" }
        )

        if ($Generated.Count -lt 1) {
            throw "Missing generated source: ${Stem}_gen.cpp"
        }

        Write-Host "COMPILED: $Stem"
        Write-Host "  OBJ: $($Obj[0].FullName)"
        Write-Host "  GEN: $($Generated[0].FullName)"
    }

    Section "VERIFY REBUILT RUNTIME"

    $BuiltForte = Join-Path $BuildDir "src\Debug\forte.exe"
    Require-File $BuiltForte "Rebuilt forte.exe"

    Copy-Item `
        -LiteralPath $BuiltForte `
        -Destination (Join-Path $RuntimeDir "forte.exe")

    Copy-Item `
        -LiteralPath $LocalOpenDll `
        -Destination (Join-Path $RuntimeDir "open62541.dll")

    $BuiltHash = (Get-FileHash -LiteralPath $BuiltForte -Algorithm SHA256).Hash

    Write-Host "Rebuilt forte.exe SHA256:   $BuiltHash"
    Write-Host "Validated forte.exe SHA256: $ExpectedRuntimeSha256"

    if ($BuiltHash -eq $ExpectedRuntimeSha256) {
        Write-Host "BYTE-IDENTICAL REBUILD: YES"
    }
    if ($BuiltHash -ne $ExpectedRuntimeSha256) {
        Write-Host "BYTE-IDENTICAL REBUILD: NO"
        Write-Host "NOTE: source-equivalent builds are not required to be byte-identical."
    }

    Write-Host ""
    Write-Host "REPRODUCIBLE BUILD: PASSED"
    Write-Host "CUSTOM MPC FB TYPES COMPILED: YES"
    Write-Host "REBUILT FORTE EXECUTABLE EXISTS: YES"
    Write-Host "NETWORK DOWNLOADS: NO"
    Write-Host "PLC/GATEWAY ACCESS: NO"
    Write-Host "DEPLOYMENT: NO"
    Write-Host "REAL MPC AUTHORIZED: NO"
    Write-Host "OUTPUT: $OutputRoot"
}
finally {
    if ($WorktreeAdded) {
        Section "REMOVE TEMPORARY FORTE WORKTREE"

        git -C $ForteSource worktree remove --force $Worktree
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove temporary FORTE worktree registration."
        }
    }
}