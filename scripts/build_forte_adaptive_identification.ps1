[CmdletBinding()]
param(
    [string]$ForteSource = "$env:USERPROFILE\4diac\4diac-forte",
    [string]$ExportDirectory = "C:\Projetos\forte-adaptive-identification\external-modules\ADAPTIVE_IDENTIFICATION"
)
$ErrorActionPreference = "Stop"
$revision = "7c8b6296227fa292c13d71d2958a404c6db03e53"
foreach ($tool in @("git", "cmake")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Missing tool: $tool" }
}
if (-not (Test-Path -LiteralPath (Join-Path $ForteSource "CMakeLists.txt"))) { throw "FORTE source missing." }
& git -C $ForteSource cat-file -e "$revision^{commit}"
if ($LASTEXITCODE -ne 0) { throw "Expected FORTE commit unavailable." }
$files = @{}
foreach ($name in @("INPUT_SEQUENCE_REPLAY.cpp", "INPUT_SEQUENCE_REPLAY.h", "OUTPUT_HISTORY.cpp", "OUTPUT_HISTORY.h", "SECOND_ORDER_PROCESS.cpp", "SECOND_ORDER_PROCESS.h", "RLS_PARAMETER_ESTIMATOR.cpp", "RLS_PARAMETER_ESTIMATOR.h")) {
    $exportMatches = @(Get-ChildItem -LiteralPath $ExportDirectory -Recurse -File -Filter $name)
    if ($exportMatches.Count -ne 1) { throw "Expected exactly one exported $name; found $($exportMatches.Count)." }
    if ($exportMatches[0].Length -eq 0) { throw "Empty export: $name" }
    $files[$name] = $exportMatches[0].FullName
}
$root = Join-Path "C:\Projetos\forte-adaptive-identification\runs" (Get-Date -Format "yyyyMMdd-HHmmss-fff")
$source = Join-Path $root "source"
$build = Join-Path $root "build"
$external = Join-Path $root "external-modules"
$module = Join-Path $external "ADAPTIVE_IDENTIFICATION"
if (Test-Path -LiteralPath $root) { throw "Output already exists: $root" }
New-Item -ItemType Directory -Path $module -Force | Out-Null
$log = Join-Path $root "build-transcript.txt"
Start-Transcript -Path $log | Out-Null
try {
    Write-Host "Isolated build: $root"
    & git -C $ForteSource worktree add --detach $source $revision
    if ($LASTEXITCODE -ne 0) { throw "Cannot create isolated source worktree." }
    # Compatibility change in the isolated copy only, matching the preserved build patch.
    $cmakeFile = Join-Path $source "CMakeLists.txt"
    $text = [IO.File]::ReadAllText($cmakeFile)
    $old = "CMAKE_MINIMUM_REQUIRED(VERSION 2.6)"
    if (-not $text.Contains($old)) { throw "Unexpected CMake minimum version declaration." }
    [IO.File]::WriteAllText($cmakeFile, $text.Replace($old, "CMAKE_MINIMUM_REQUIRED(VERSION 3.5...3.20)"), [Text.UTF8Encoding]::new($false))
    foreach ($name in $files.Keys) {
        Copy-Item -LiteralPath $files[$name] -Destination (Join-Path $module $name)
    }
    [IO.File]::WriteAllText((Join-Path $module "CMakeLists.txt"), "forte_add_directory_module()`nforte_add_all_sourcefiles()`n", [Text.UTF8Encoding]::new($false))
    Get-ChildItem -LiteralPath $module -File | Get-FileHash -Algorithm SHA256 | Format-List
    $argsCmake = @(
        "-S", $source, "-B", $build, "-G", "Visual Studio 18 2026", "-A", "x64",
        "-DFORTE_ARCHITECTURE=Win32",
        "-DFORTE_BUILD_EXECUTABLE=ON", "-DFORTE_BUILD_SHARED_LIBRARY=OFF", "-DFORTE_BUILD_STATIC_LIBRARY=OFF",
        "-DFORTE_COM_ETH=ON", "-DFORTE_COM_FBDK=ON", "-DFORTE_COM_LOCAL=ON",
        "-DFORTE_COM_OPC_UA=OFF",
        "-DFORTE_EXTERNAL_MODULES_DIRECTORY=$($external.Replace('\','/'))",
        "-DFORTE_MODULE_EXTERNAL_ADAPTIVE_IDENTIFICATION=ON",
        "-DFORTE_MODULE_IEC61131=ON", "-DFORTE_MODULE_UTILS=ON", "-DFORTE_MODULE_CONVERT=ON",
        "-DFORTE_SUPPORT_MONITORING=ON", "-DFORTE_SUPPORT_QUERY_CMD=ON",
        "-DFORTE_SUPPORT_BOOT_FILE=OFF",
        "-DFORTE_USE_REAL_DATATYPE=ON", "-DFORTE_USE_64BIT_DATATYPES=ON",
        "-DFORTE_TESTS=OFF", "-DFORTE_SYSTEM_TESTS=OFF"
    )
    & cmake @argsCmake
    if ($LASTEXITCODE -ne 0) { throw "CMake configuration failed. See $log" }
    & cmake --build $build --config Debug --parallel 4
    if ($LASTEXITCODE -ne 0) { throw "Compilation failed. See $log" }
    foreach ($name in @("INPUT_SEQUENCE_REPLAY", "OUTPUT_HISTORY", "SECOND_ORDER_PROCESS", "RLS_PARAMETER_ESTIMATOR")) {
        $objects = @(Get-ChildItem -LiteralPath $build -Recurse -File -Filter "$name.obj")
        if ($objects.Count -eq 0) { throw "No compiled object found for $name." }
    }
    $exe = Join-Path $build "src\Debug\forte.exe"
    if (-not (Test-Path -LiteralPath $exe)) { throw "Executable not found at expected path: $exe" }
    Write-Host "BUILD COMPLETED: $exe" -ForegroundColor Green
    Get-FileHash -LiteralPath $exe -Algorithm SHA256 | Format-List
    Write-Host "Runtime NOT started. No application deployed. Log: $log"
}
finally {
    Stop-Transcript | Out-Null
}
