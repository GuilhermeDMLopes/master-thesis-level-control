[CmdletBinding()]
param(
    [string]$WorkingProjectRoot = "C:\projects\mestrado_guilherme_watchdog_v2_20260403-021715",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Title {
    param([string]$Text)

    Write-Host ""
    Write-Host ("=" * 88)
    Write-Host $Text
    Write-Host ("=" * 88)
}

function Read-AllText {
    param([string]$Path)

    $reader = New-Object System.IO.StreamReader(
        $Path,
        [System.Text.Encoding]::Default,
        $true
    )

    try {
        $text = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }

    return $text
}

function Add-ValidationResult {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Category,
        [string]$Name,
        [bool]$Passed,
        [string]$Details,
        [bool]$Blocking
    )

    $record = [PSCustomObject]@{
        Category = $Category
        Name = $Name
        Passed = $Passed
        Blocking = $Blocking
        Details = $Details
    }

    [void]$Results.Add($record)

    if ($Passed) {
        $status = "PASS"
    }
    else {
        $status = "FAIL"
    }

    if ($Blocking) {
        $importance = "blocking"
    }
    else {
        $importance = "informational"
    }

    Write-Host (
        "[{0}] [{1}] {2}: {3}" -f
        $status,
        $importance,
        $Name,
        $Details
    )
}

function Test-Regex {
    param(
        [string]$Text,
        [string]$Pattern
    )

    return [regex]::IsMatch(
        $Text,
        $Pattern,
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
}

function Get-RelativePath {
    param(
        [string]$BasePath,
        [string]$FullPath
    )

    return $FullPath.Substring(
        $BasePath.Length
    ).TrimStart("\")
}

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = $scriptDirectory
}

Write-Title "WATCHDOG PRE-REBUILD VALIDATOR V2"

Write-Host "Read-only validation."
Write-Host "No Build, Transfer, PLC connection, or PLC write is performed."

if (-not (Test-Path -LiteralPath $WorkingProjectRoot -PathType Container)) {
    $WorkingProjectRoot = (
        Read-Host "Enter the full watchdog_v2 working-copy directory"
    ).Trim('"')
}

if (-not (Test-Path -LiteralPath $WorkingProjectRoot -PathType Container)) {
    throw (
        "Working project directory not found: {0}" -f
        $WorkingProjectRoot
    )
}

$projectRoot = (Resolve-Path -LiteralPath $WorkingProjectRoot).Path

if (-not (Test-Path -LiteralPath $OutputRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
}

$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$reportRoot = Join-Path $OutputRoot ("WatchdogPreRebuildValidationV2-" + $runId)
$reportZip = $reportRoot + ".zip"
$checksPath = Join-Path $reportRoot "01-checks.csv"
$summaryPath = Join-Path $reportRoot "00-summary.txt"
$uadContextPath = Join-Path $reportRoot "02-opcua-context.txt"
$taskContextPath = Join-Path $reportRoot "03-task-context.txt"
$manifestPath = Join-Path $reportRoot "04-manifest-sha256.csv"
$contextPath = Join-Path $scriptDirectory "rebuild-validation-context-v2.json"

New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null

$results = New-Object System.Collections.ArrayList
$uadContext = New-Object System.Collections.Generic.List[string]
$taskContext = New-Object System.Collections.Generic.List[string]

Write-Title "PROJECT AND BACKUP"

$projectLeaf = Split-Path -Leaf $projectRoot

Add-ValidationResult `
    -Results $results `
    -Category "Project" `
    -Name "Working-copy folder name" `
    -Passed ($projectLeaf -match "_watchdog_v2_") `
    -Details $projectLeaf `
    -Blocking $true

$projectParent = Split-Path -Parent $projectRoot
$baseName = [regex]::Replace(
    $projectLeaf,
    "_watchdog_v2_\d{8}-\d{6}$",
    ""
)

$backupFolders = @(
    Get-ChildItem `
        -LiteralPath $projectParent `
        -Directory `
        -Filter ($baseName + "_pre_watchdog_*") `
        -ErrorAction SilentlyContinue
)

Add-ValidationResult `
    -Results $results `
    -Category "Project" `
    -Name "Timestamped backup folder" `
    -Passed ($backupFolders.Count -ge 1) `
    -Details ("Found {0} matching folder(s)." -f $backupFolders.Count) `
    -Blocking $true

$apjFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "*.apj" `
        -ErrorAction SilentlyContinue
)

Add-ValidationResult `
    -Results $results `
    -Category "Project" `
    -Name "Single .apj project file" `
    -Passed ($apjFiles.Count -eq 1) `
    -Details ("Found {0} .apj file(s)." -f $apjFiles.Count) `
    -Blocking $true

Write-Title "VARIABLE DECLARATIONS"

$variableFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "*.var" `
        -ErrorAction SilentlyContinue |
    Where-Object {
        (Read-AllText -Path $_.FullName).Contains(
            "MASTER_THESIS_WATCHDOG_V2_VARIABLES"
        )
    }
)

Add-ValidationResult `
    -Results $results `
    -Category "Variables" `
    -Name "Single watchdog variable file" `
    -Passed ($variableFiles.Count -eq 1) `
    -Details ("Found {0} matching file(s)." -f $variableFiles.Count) `
    -Blocking $true

if ($variableFiles.Count -eq 1) {
    $variablePath = $variableFiles[0].FullName
    $variableText = Read-AllText -Path $variablePath

    $requiredDeclarations = @(
        [PSCustomObject]@{ Name = "Nivel : INT"; Pattern = "(?im)^\s*Nivel\s*:\s*INT\s*;" },
        [PSCustomObject]@{ Name = "Enable : BOOL"; Pattern = "(?im)^\s*Enable\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "DAC : INT"; Pattern = "(?im)^\s*DAC\s*:\s*INT\s*;" },
        [PSCustomObject]@{ Name = "Heartbeat : UDINT"; Pattern = "(?im)^\s*Heartbeat\s*:\s*UDINT\s*;" },
        [PSCustomObject]@{ Name = "SafetyReset : BOOL"; Pattern = "(?im)^\s*SafetyReset\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "EnableOut : BOOL"; Pattern = "(?im)^\s*EnableOut\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "DACOut : INT"; Pattern = "(?im)^\s*DACOut\s*:\s*INT\s*;" },
        [PSCustomObject]@{ Name = "WatchdogHealthy : BOOL"; Pattern = "(?im)^\s*WatchdogHealthy\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "WatchdogTripped : BOOL"; Pattern = "(?im)^\s*WatchdogTripped\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "AppliedEnable : BOOL"; Pattern = "(?im)^\s*AppliedEnable\s*:\s*BOOL\s*;" },
        [PSCustomObject]@{ Name = "AppliedDAC : INT"; Pattern = "(?im)^\s*AppliedDAC\s*:\s*INT\s*;" },
        [PSCustomObject]@{ Name = "WdTimer : TON"; Pattern = "(?im)^\s*WdTimer\s*:\s*TON\s*;" }
    )

    foreach ($declaration in $requiredDeclarations) {
        $present = Test-Regex `
            -Text $variableText `
            -Pattern $declaration.Pattern

        Add-ValidationResult `
            -Results $results `
            -Category "Variables" `
            -Name $declaration.Name `
            -Passed $present `
            -Details $variablePath `
            -Blocking $true
    }
}

Write-Title "WATCHDOG LOGIC"

$routines = @(
    [PSCustomObject]@{
        Role = "INIT"
        Marker = "MASTER_THESIS_WATCHDOG_V2_INIT"
        Patterns = @(
            "Enable\s*:=\s*FALSE\s*;",
            "DAC\s*:=\s*0\s*;",
            "EnableOut\s*:=\s*FALSE\s*;",
            "DACOut\s*:=\s*0\s*;",
            "WdTripLatched\s*:=\s*TRUE\s*;"
        )
    },
    [PSCustomObject]@{
        Role = "CYCLIC"
        Marker = "MASTER_THESIS_WATCHDOG_V2_CYCLIC"
        Patterns = @(
            "Heartbeat\s*<>\s*WdHeartbeatLast",
            "WdTimer\s*\(",
            "PT\s*:=\s*T#1s",
            "WdTripLatched\s*:=\s*TRUE\s*;",
            "WatchdogHealthy\s*:=",
            "AppliedEnable\s*:=\s*FALSE\s*;",
            "AppliedDAC\s*:=\s*0\s*;",
            "EnableOut\s*:=\s*AppliedEnable\s*;",
            "DACOut\s*:=\s*AppliedDAC\s*;"
        )
    },
    [PSCustomObject]@{
        Role = "EXIT"
        Marker = "MASTER_THESIS_WATCHDOG_V2_EXIT"
        Patterns = @(
            "Enable\s*:=\s*FALSE\s*;",
            "DAC\s*:=\s*0\s*;",
            "EnableOut\s*:=\s*FALSE\s*;",
            "DACOut\s*:=\s*0\s*;",
            "WdTripLatched\s*:=\s*TRUE\s*;"
        )
    }
)

foreach ($routine in $routines) {
    $routineFiles = @(
        Get-ChildItem `
            -LiteralPath $projectRoot `
            -Recurse `
            -File `
            -Filter "*.st" `
            -ErrorAction SilentlyContinue |
        Where-Object {
            (Read-AllText -Path $_.FullName).Contains(
                $routine.Marker
            )
        }
    )

    Add-ValidationResult `
        -Results $results `
        -Category "Logic" `
        -Name ($routine.Role + " marker") `
        -Passed ($routineFiles.Count -eq 1) `
        -Details ("Found {0} matching file(s)." -f $routineFiles.Count) `
        -Blocking $true

    if ($routineFiles.Count -eq 1) {
        $routinePath = $routineFiles[0].FullName
        $routineText = Read-AllText -Path $routinePath

        foreach ($pattern in $routine.Patterns) {
            $present = Test-Regex `
                -Text $routineText `
                -Pattern $pattern

            Add-ValidationResult `
                -Results $results `
                -Category "Logic" `
                -Name ($routine.Role + " contains " + $pattern) `
                -Passed $present `
                -Details $routinePath `
                -Blocking $true
        }
    }
}

Write-Title "I/O MAPPING"

$ioMapFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "IoMap.iom" `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $ioTextCandidate = Read-AllText -Path $_.FullName

        (
            $ioTextCandidate.Contains("::Program:Nivel")
        ) -or (
            $ioTextCandidate.Contains("::Program:EnableOut")
        ) -or (
            $ioTextCandidate.Contains("::Program:DACOut")
        )
    }
)

Add-ValidationResult `
    -Results $results `
    -Category "I/O Mapping" `
    -Name "Single relevant IoMap.iom" `
    -Passed ($ioMapFiles.Count -eq 1) `
    -Details ("Found {0} relevant file(s)." -f $ioMapFiles.Count) `
    -Blocking $true

if ($ioMapFiles.Count -eq 1) {
    $ioMapPath = $ioMapFiles[0].FullName
    $ioMapText = Read-AllText -Path $ioMapPath

    Add-ValidationResult `
        -Results $results `
        -Category "I/O Mapping" `
        -Name "Nivel input mapping preserved" `
        -Passed ($ioMapText.Contains("::Program:Nivel")) `
        -Details $ioMapPath `
        -Blocking $true

    Add-ValidationResult `
        -Results $results `
        -Category "I/O Mapping" `
        -Name "Analog output mapped to DACOut" `
        -Passed ($ioMapText.Contains("::Program:DACOut")) `
        -Details $ioMapPath `
        -Blocking $true

    Add-ValidationResult `
        -Results $results `
        -Category "I/O Mapping" `
        -Name "Digital output mapped to EnableOut" `
        -Passed ($ioMapText.Contains("::Program:EnableOut")) `
        -Details $ioMapPath `
        -Blocking $true

    $oldEnableMapping = [regex]::IsMatch(
        $ioMapText,
        "::Program:Enable(?![A-Za-z0-9_])"
    )

    $oldDacMapping = [regex]::IsMatch(
        $ioMapText,
        "::Program:DAC(?![A-Za-z0-9_])"
    )

    Add-ValidationResult `
        -Results $results `
        -Category "I/O Mapping" `
        -Name "Old direct Enable mapping removed" `
        -Passed (-not $oldEnableMapping) `
        -Details $ioMapPath `
        -Blocking $true

    Add-ValidationResult `
        -Results $results `
        -Category "I/O Mapping" `
        -Name "Old direct DAC mapping removed" `
        -Passed (-not $oldDacMapping) `
        -Details $ioMapPath `
        -Blocking $true
}

Write-Title "OPC UA DEFAULT VIEW"

$uadFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "*.uad" `
        -ErrorAction SilentlyContinue
)

Add-ValidationResult `
    -Results $results `
    -Category "OPC UA" `
    -Name "Single .uad file" `
    -Passed ($uadFiles.Count -eq 1) `
    -Details ("Found {0} .uad file(s)." -f $uadFiles.Count) `
    -Blocking $true

if ($uadFiles.Count -eq 1) {
    $uadPath = $uadFiles[0].FullName
    $uadText = Read-AllText -Path $uadPath

    $requiredOpcUaVariables = @(
        "Nivel",
        "Enable",
        "DAC",
        "Heartbeat",
        "SafetyReset",
        "WatchdogHealthy",
        "WatchdogTripped",
        "AppliedEnable",
        "AppliedDAC"
    )

    foreach ($name in $requiredOpcUaVariables) {
        $pattern = (
            "(?<![A-Za-z0-9_])" +
            [regex]::Escape($name) +
            "(?![A-Za-z0-9_])"
        )

        $present = Test-Regex `
            -Text $uadText `
            -Pattern $pattern

        Add-ValidationResult `
            -Results $results `
            -Category "OPC UA" `
            -Name ("Published variable: " + $name) `
            -Passed $present `
            -Details $uadPath `
            -Blocking $true

        $matches = @(
            Select-String `
                -LiteralPath $uadPath `
                -Pattern $name `
                -SimpleMatch `
                -Context 3,5 `
                -ErrorAction SilentlyContinue
        )

        foreach ($match in $matches) {
            $uadContext.Add("")
            $uadContext.Add(
                (
                    "{0}:{1} | {2}" -f
                    $match.Path,
                    $match.LineNumber,
                    $name
                )
            )

            foreach ($line in $match.Context.PreContext) {
                $uadContext.Add("  BEFORE | " + $line)
            }

            $uadContext.Add("  MATCH  | " + $match.Line)

            foreach ($line in $match.Context.PostContext) {
                $uadContext.Add("  AFTER  | " + $line)
            }
        }
    }

    $forbiddenOpcUaVariables = @(
        "EnableOut",
        "DACOut"
    )

    foreach ($name in $forbiddenOpcUaVariables) {
        $pattern = (
            "(?<![A-Za-z0-9_])" +
            [regex]::Escape($name) +
            "(?![A-Za-z0-9_])"
        )

        $present = Test-Regex `
            -Text $uadText `
            -Pattern $pattern

        Add-ValidationResult `
            -Results $results `
            -Category "OPC UA" `
            -Name ("Not published: " + $name) `
            -Passed (-not $present) `
            -Details $uadPath `
            -Blocking $true
    }

    $internalWdPresent = Test-Regex `
        -Text $uadText `
        -Pattern "(?<![A-Za-z0-9_])Wd[A-Za-z0-9_]+"

    Add-ValidationResult `
        -Results $results `
        -Category "OPC UA" `
        -Name "Internal Wd variables are not published" `
        -Passed (-not $internalWdPresent) `
        -Details $uadPath `
        -Blocking $true
}

[System.IO.File]::WriteAllLines(
    $uadContextPath,
    $uadContext,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Title "TASK CONFIGURATION EVIDENCE"

$taskPatterns = @(
    "TaskClass",
    "Task Class",
    "CycleTime",
    "Cycle Time",
    "Interval",
    "Tolerance",
    "Priority"
)

$taskExtensions = @(
    ".apj",
    ".pkg",
    ".xml",
    ".cfg",
    ".hw",
    ".iom",
    ".txt"
)

$taskFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
    Where-Object {
        (
            $taskExtensions -contains $_.Extension.ToLowerInvariant()
        ) -and (
            $_.Length -le 20MB
        )
    }
)

foreach ($taskFile in $taskFiles) {
    $taskMatches = @(
        Select-String `
            -LiteralPath $taskFile.FullName `
            -Pattern $taskPatterns `
            -SimpleMatch `
            -Context 2,4 `
            -ErrorAction SilentlyContinue
    )

    foreach ($match in $taskMatches) {
        $taskContext.Add("")
        $taskContext.Add(
            (
                "{0}:{1} | Pattern={2}" -f
                $match.Path,
                $match.LineNumber,
                $match.Pattern
            )
        )

        foreach ($line in $match.Context.PreContext) {
            $taskContext.Add("  BEFORE | " + $line)
        }

        $taskContext.Add("  MATCH  | " + $match.Line)

        foreach ($line in $match.Context.PostContext) {
            $taskContext.Add("  AFTER  | " + $line)
        }
    }
}

[System.IO.File]::WriteAllLines(
    $taskContextPath,
    $taskContext,
    [System.Text.UTF8Encoding]::new($false)
)

Add-ValidationResult `
    -Results $results `
    -Category "Task" `
    -Name "Task evidence collected" `
    -Passed ($taskContext.Count -gt 0) `
    -Details ("Collected {0} context line(s)." -f $taskContext.Count) `
    -Blocking $false

Write-Title "FINAL VERDICT"

$blockingFailures = @(
    $results |
    Where-Object {
        $_.Blocking -and (-not $_.Passed)
    }
)

if ($blockingFailures.Count -eq 0) {
    $staticStatus = "PASSED"
    $readyForRebuild = "YES"
    $validationPassed = $true
}
else {
    $staticStatus = "FAILED"
    $readyForRebuild = "NO"
    $validationPassed = $false
}

Write-Host ""
Write-Host ("STATIC PROJECT VALIDATION: {0}" -f $staticStatus)
Write-Host ("READY FOR MANUAL REBUILD CONFIGURATION: {0}" -f $readyForRebuild)
Write-Host "READY FOR PLC TRANSFER: NO"
Write-Host ""
Write-Host "Exact OPC UA read/write permissions still require visual review."
Write-Host "Do not transfer anything to the PLC."

$summaryLines = @(
    "WATCHDOG PRE-REBUILD VALIDATION V2",
    "==================================",
    "",
    ("Generated at: {0}" -f (Get-Date).ToString("o")),
    ("Working project: {0}" -f $projectRoot),
    ("Static project validation: {0}" -f $staticStatus),
    ("Ready for manual Rebuild Configuration: {0}" -f $readyForRebuild),
    "Ready for PLC transfer: NO",
    "",
    ("Blocking failures: {0}" -f $blockingFailures.Count),
    "",
    "Manual review still required:",
    "- confirm OPC UA read/write permissions visually;",
    "- record task name, period, tolerance, and priority;",
    "- run only Project -> Rebuild Configuration;",
    "- do not Transfer, Install, Build and Transfer, or go Online."
)

[System.IO.File]::WriteAllLines(
    $summaryPath,
    $summaryLines,
    [System.Text.UTF8Encoding]::new($false)
)

$results |
    Export-Csv `
        -LiteralPath $checksPath `
        -NoTypeInformation `
        -Encoding UTF8

$context = [ordered]@{
    WorkingProjectRoot = $projectRoot
    ValidationTime = (Get-Date).ToString("o")
    ValidationPassed = $validationPassed
    ReadyForManualRebuild = $validationPassed
    PreRebuildReportZip = $reportZip
}

$context |
    ConvertTo-Json |
    Set-Content `
        -LiteralPath $contextPath `
        -Encoding UTF8

$manifestRows = @(
    Get-ChildItem `
        -LiteralPath $reportRoot `
        -Recurse `
        -File |
    Where-Object {
        $_.FullName -ne $manifestPath
    } |
    Sort-Object FullName |
    ForEach-Object {
        [PSCustomObject]@{
            RelativePath = Get-RelativePath `
                -BasePath $reportRoot `
                -FullPath $_.FullName
            Length = $_.Length
            SHA256 = (
                Get-FileHash `
                    -Algorithm SHA256 `
                    -LiteralPath $_.FullName
            ).Hash
        }
    }
)

$manifestRows |
    Export-Csv `
        -LiteralPath $manifestPath `
        -NoTypeInformation `
        -Encoding UTF8

if (Test-Path -LiteralPath $reportZip) {
    Remove-Item -LiteralPath $reportZip -Force
}

Compress-Archive `
    -Path (Join-Path $reportRoot "*") `
    -DestinationPath $reportZip `
    -CompressionLevel Optimal

$reportHash = (
    Get-FileHash `
        -Algorithm SHA256 `
        -LiteralPath $reportZip
).Hash

Write-Host ""
Write-Host ("Report ZIP: {0}" -f $reportZip)
Write-Host ("Report SHA256: {0}" -f $reportHash)

if (-not $validationPassed) {
    exit 2
}
