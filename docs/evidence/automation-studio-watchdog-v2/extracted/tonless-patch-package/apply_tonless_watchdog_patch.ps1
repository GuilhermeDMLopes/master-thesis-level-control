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

function Read-TextFile {
    param([string]$Path)

    $reader = New-Object System.IO.StreamReader(
        $Path,
        [System.Text.Encoding]::Default,
        $true
    )

    try {
        $text = $reader.ReadToEnd()
        $encoding = $reader.CurrentEncoding
    }
    finally {
        $reader.Dispose()
    }

    return [PSCustomObject]@{
        Text = $text
        Encoding = $encoding
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Text,
        [System.Text.Encoding]$Encoding
    )

    [System.IO.File]::WriteAllText(
        $Path,
        $Text,
        $Encoding
    )
}

function Replace-ExactlyOnce {
    param(
        [string]$Text,
        [string]$Pattern,
        [string]$Replacement,
        [string]$Description
    )

    $matches = @(
        [regex]::Matches(
            $Text,
            $Pattern,
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
            [System.Text.RegularExpressions.RegexOptions]::Multiline -bor
            [System.Text.RegularExpressions.RegexOptions]::Singleline
        )
    )

    if ($matches.Count -ne 1) {
        throw (
            "Expected exactly one match for {0}. Found {1}." -f
            $Description,
            $matches.Count
        )
    }

    return [regex]::Replace(
        $Text,
        $Pattern,
        $Replacement,
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
        [System.Text.RegularExpressions.RegexOptions]::Multiline -bor
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )
}

function Get-UniqueMarkedFile {
    param(
        [string]$Root,
        [string]$Filter,
        [string]$Marker,
        [string]$Description
    )

    $matches = @(
        Get-ChildItem `
            -LiteralPath $Root `
            -Recurse `
            -File `
            -Filter $Filter `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $content = (
                Read-TextFile `
                    -Path $_.FullName
            ).Text

            $content.Contains($Marker)
        }
    )

    if ($matches.Count -ne 1) {
        throw (
            "Expected one {0}. Found {1}." -f
            $Description,
            $matches.Count
        )
    }

    return $matches[0]
}

function Assert-Contains {
    param(
        [string]$Text,
        [string]$Pattern,
        [string]$Description
    )

    $present = [regex]::IsMatch(
        $Text,
        $Pattern,
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
        [System.Text.RegularExpressions.RegexOptions]::Multiline
    )

    if (-not $present) {
        throw (
            "Validation failed: {0}" -f
            $Description
        )
    }
}

$scriptDirectory = Split-Path `
    -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = $scriptDirectory
}

Write-Title "TONLESS WATCHDOG PATCH"

Write-Host "This script modifies only the watchdog_v2 working copy."
Write-Host "It does not connect to, build for, transfer to, or write to the PLC."
Write-Host ""

if (
    -not (
        Test-Path `
            -LiteralPath $WorkingProjectRoot `
            -PathType Container
    )
) {
    $WorkingProjectRoot = (
        Read-Host "Enter the full watchdog_v2 working-copy directory"
    ).Trim('"')
}

if (
    -not (
        Test-Path `
            -LiteralPath $WorkingProjectRoot `
            -PathType Container
    )
) {
    throw (
        "Working project directory not found: {0}" -f
        $WorkingProjectRoot
    )
}

$automationStudioProcesses = @(
    Get-CimInstance Win32_Process |
    Where-Object {
        (
            $_.Name -match "AutomationStudio|^AS4|^AS6"
        ) -or (
            $_.CommandLine -match "Automation Studio"
        )
    }
)

if ($automationStudioProcesses.Count -gt 0) {
    throw "Close Automation Studio before applying this patch."
}

$projectRoot = (
    Resolve-Path `
        -LiteralPath $WorkingProjectRoot
).Path

$projectLeaf = Split-Path `
    -Leaf $projectRoot

if ($projectLeaf -notmatch "_watchdog_v2_") {
    throw (
        "Refusing to modify a folder that is not a watchdog_v2 working copy: {0}" -f
        $projectLeaf
    )
}

if (
    -not (
        Test-Path `
            -LiteralPath $OutputRoot `
            -PathType Container
    )
) {
    New-Item `
        -ItemType Directory `
        -Path $OutputRoot `
        -Force |
        Out-Null
}

$runId = Get-Date `
    -Format "yyyyMMdd-HHmmss"

$reportRoot = Join-Path `
    $OutputRoot `
    (
        "TonlessWatchdogPatchReport-" +
        $runId
    )

$reportZip = $reportRoot + ".zip"
$backupRoot = Join-Path $reportRoot "before"
$afterRoot = Join-Path $reportRoot "after"
$summaryPath = Join-Path $reportRoot "00-summary.txt"
$manifestPath = Join-Path $reportRoot "01-manifest-sha256.csv"
$removedBackupListPath = Join-Path $reportRoot "02-moved-project-backups.txt"

New-Item `
    -ItemType Directory `
    -Path $backupRoot `
    -Force |
    Out-Null

New-Item `
    -ItemType Directory `
    -Path $afterRoot `
    -Force |
    Out-Null

Write-Title "LOCATING WATCHDOG FILES"

$variableFile = Get-UniqueMarkedFile `
    -Root $projectRoot `
    -Filter "*.var" `
    -Marker "MASTER_THESIS_WATCHDOG_V2_VARIABLES" `
    -Description "watchdog variable file"

$initFile = Get-UniqueMarkedFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -Marker "MASTER_THESIS_WATCHDOG_V2_INIT" `
    -Description "watchdog INIT file"

$cyclicFile = Get-UniqueMarkedFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -Marker "MASTER_THESIS_WATCHDOG_V2_CYCLIC" `
    -Description "watchdog CYCLIC file"

$exitFile = Get-UniqueMarkedFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -Marker "MASTER_THESIS_WATCHDOG_V2_EXIT" `
    -Description "watchdog EXIT file"

Write-Host ("Variables: {0}" -f $variableFile.FullName)
Write-Host ("INIT:      {0}" -f $initFile.FullName)
Write-Host ("CYCLIC:    {0}" -f $cyclicFile.FullName)
Write-Host ("EXIT:      {0}" -f $exitFile.FullName)

$sourceFiles = @(
    $variableFile,
    $initFile,
    $cyclicFile,
    $exitFile
)

foreach ($sourceFile in $sourceFiles) {
    Copy-Item `
        -LiteralPath $sourceFile.FullName `
        -Destination (
            Join-Path `
                $backupRoot `
                $sourceFile.Name
        ) `
        -Force
}

Write-Title "MOVING NON-PROJECT BACKUP FILES"

$embeddedBackups = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "*.pre_finalizer_*.bak" `
        -ErrorAction SilentlyContinue
)

$movedBackupLines = New-Object System.Collections.Generic.List[string]
$externalBackupDirectory = Join-Path `
    $reportRoot `
    "moved-project-backups"

New-Item `
    -ItemType Directory `
    -Path $externalBackupDirectory `
    -Force |
    Out-Null

foreach ($embeddedBackup in $embeddedBackups) {
    $destinationName = (
        $embeddedBackup.Directory.Name +
        "__" +
        $embeddedBackup.Name
    )

    $destinationPath = Join-Path `
        $externalBackupDirectory `
        $destinationName

    Move-Item `
        -LiteralPath $embeddedBackup.FullName `
        -Destination $destinationPath `
        -Force

    $movedBackupLines.Add(
        (
            "{0} -> {1}" -f
            $embeddedBackup.FullName,
            $destinationPath
        )
    )
}

[System.IO.File]::WriteAllLines(
    $removedBackupListPath,
    $movedBackupLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host (
    "Moved {0} embedded backup file(s) outside the project." -f
    $embeddedBackups.Count
)

Write-Title "REPLACING TON WITH A 100 MS CYCLE COUNTER"

$variableData = Read-TextFile `
    -Path $variableFile.FullName

$variableText = $variableData.Text

if ($variableText.Contains("MASTER_THESIS_WATCHDOG_TONLESS_V1")) {
    throw "The TON-less watchdog patch is already present."
}

$variableReplacement = @'
    (* MASTER_THESIS_WATCHDOG_TONLESS_V1 *)
    WdCyclesWithoutHeartbeat : UDINT;
    WdTimeoutCycles : UDINT;
    WdTimedOut : BOOL;
'@

$variableText = Replace-ExactlyOnce `
    -Text $variableText `
    -Pattern "(?m)^\s*WdTimer\s*:\s*TON\s*;\s*$" `
    -Replacement $variableReplacement.TrimEnd() `
    -Description "WdTimer TON declaration"

Write-TextFile `
    -Path $variableFile.FullName `
    -Text $variableText `
    -Encoding $variableData.Encoding

$initData = Read-TextFile `
    -Path $initFile.FullName

$initReplacement = @'
WdCyclesWithoutHeartbeat := 0;
WdTimeoutCycles := 10;
WdTimedOut := TRUE;
'@

$initText = Replace-ExactlyOnce `
    -Text $initData.Text `
    -Pattern "WdTimer\s*\(\s*IN\s*:=\s*FALSE\s*,\s*PT\s*:=\s*T#1s\s*\)\s*;" `
    -Replacement $initReplacement.TrimEnd() `
    -Description "INIT WdTimer call"

Write-TextFile `
    -Path $initFile.FullName `
    -Text $initText `
    -Encoding $initData.Encoding

$cyclicData = Read-TextFile `
    -Path $cyclicFile.FullName

$cyclicCounterLogic = @'
IF WdHeartbeatChanged THEN
    WdHeartbeatLast := Heartbeat;
    WdHeartbeatSeen := TRUE;
    WdCyclesWithoutHeartbeat := 0;

ELSIF WdHeartbeatSeen THEN
    IF WdCyclesWithoutHeartbeat < WdTimeoutCycles THEN
        WdCyclesWithoutHeartbeat := WdCyclesWithoutHeartbeat + 1;
    END_IF;

ELSE
    WdCyclesWithoutHeartbeat := 0;
END_IF;

WdTimedOut := (
    WdHeartbeatSeen
    AND
    (WdCyclesWithoutHeartbeat >= WdTimeoutCycles)
);
'@

$cyclicText = Replace-ExactlyOnce `
    -Text $cyclicData.Text `
    -Pattern "IF\s+WdHeartbeatChanged\s+THEN\s*WdHeartbeatLast\s*:=\s*Heartbeat\s*;\s*WdHeartbeatSeen\s*:=\s*TRUE\s*;\s*END_IF\s*;\s*WdTimer\s*\(\s*IN\s*:=\s*\(\s*WdHeartbeatSeen\s*AND\s+NOT\s+WdHeartbeatChanged\s*\)\s*,\s*PT\s*:=\s*T#1s\s*\)\s*;" `
    -Replacement $cyclicCounterLogic.TrimEnd() `
    -Description "CYCLIC heartbeat and WdTimer logic"

$cyclicText = [regex]::Replace(
    $cyclicText,
    "\bWdTimer\.Q\b",
    "WdTimedOut",
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)

Write-TextFile `
    -Path $cyclicFile.FullName `
    -Text $cyclicText `
    -Encoding $cyclicData.Encoding

$exitData = Read-TextFile `
    -Path $exitFile.FullName

$exitReplacement = @'
WdCyclesWithoutHeartbeat := 0;
WdTimedOut := TRUE;
'@

$exitText = Replace-ExactlyOnce `
    -Text $exitData.Text `
    -Pattern "WdTimer\s*\(\s*IN\s*:=\s*FALSE\s*,\s*PT\s*:=\s*T#1s\s*\)\s*;" `
    -Replacement $exitReplacement.TrimEnd() `
    -Description "EXIT WdTimer call"

Write-TextFile `
    -Path $exitFile.FullName `
    -Text $exitText `
    -Encoding $exitData.Encoding

Write-Title "VALIDATING PATCH"

$finalVariableText = (
    Read-TextFile `
        -Path $variableFile.FullName
).Text

$finalInitText = (
    Read-TextFile `
        -Path $initFile.FullName
).Text

$finalCyclicText = (
    Read-TextFile `
        -Path $cyclicFile.FullName
).Text

$finalExitText = (
    Read-TextFile `
        -Path $exitFile.FullName
).Text

Assert-Contains `
    -Text $finalVariableText `
    -Pattern "(?im)^\s*WdCyclesWithoutHeartbeat\s*:\s*UDINT\s*;" `
    -Description "WdCyclesWithoutHeartbeat declaration"

Assert-Contains `
    -Text $finalVariableText `
    -Pattern "(?im)^\s*WdTimeoutCycles\s*:\s*UDINT\s*;" `
    -Description "WdTimeoutCycles declaration"

Assert-Contains `
    -Text $finalVariableText `
    -Pattern "(?im)^\s*WdTimedOut\s*:\s*BOOL\s*;" `
    -Description "WdTimedOut declaration"

if (
    $finalVariableText -match "(?im)^\s*WdTimer\s*:\s*TON\s*;"
) {
    throw "Validation failed: WdTimer TON declaration remains."
}

if (
    $finalInitText -match "\bWdTimer\b"
) {
    throw "Validation failed: WdTimer remains in INIT."
}

if (
    $finalCyclicText -match "\bWdTimer\b"
) {
    throw "Validation failed: WdTimer remains in CYCLIC."
}

if (
    $finalExitText -match "\bWdTimer\b"
) {
    throw "Validation failed: WdTimer remains in EXIT."
}

Assert-Contains `
    -Text $finalInitText `
    -Pattern "WdTimeoutCycles\s*:=\s*10\s*;" `
    -Description "10-cycle timeout initialization"

Assert-Contains `
    -Text $finalCyclicText `
    -Pattern "WdCyclesWithoutHeartbeat\s*:=\s*WdCyclesWithoutHeartbeat\s*\+\s*1\s*;" `
    -Description "heartbeat timeout counter increment"

Assert-Contains `
    -Text $finalCyclicText `
    -Pattern "WdCyclesWithoutHeartbeat\s*>=\s*WdTimeoutCycles" `
    -Description "heartbeat timeout comparison"

Assert-Contains `
    -Text $finalCyclicText `
    -Pattern "EnableOut\s*:=\s*AppliedEnable\s*;" `
    -Description "physical Enable output gate"

Assert-Contains `
    -Text $finalCyclicText `
    -Pattern "DACOut\s*:=\s*AppliedDAC\s*;" `
    -Description "physical DAC output gate"

foreach ($sourceFile in $sourceFiles) {
    Copy-Item `
        -LiteralPath $sourceFile.FullName `
        -Destination (
            Join-Path `
                $afterRoot `
                $sourceFile.Name
        ) `
        -Force
}

Write-Host "TON-less watchdog patch validation: PASSED"

$summaryLines = @(
    "TONLESS WATCHDOG PATCH",
    "======================",
    "",
    ("Generated at: {0}" -f (Get-Date).ToString("o")),
    ("Working project: {0}" -f $projectRoot),
    "",
    "Change applied:",
    "- removed dependency on undefined IEC TON data type;",
    "- added UDINT cycle counter;",
    "- configured 10 cycles at the existing 100 ms task period;",
    "- effective nominal watchdog timeout: approximately 1 second;",
    "- preserved latched trip and safe output gate;",
    "- removed OpcUaMap.uad.pre_finalizer_*.bak from the project tree.",
    "",
    "Validation result: PASSED",
    "Ready for manual Rebuild Configuration: YES",
    "Ready for PLC transfer: NO",
    "",
    "Next action:",
    "Open the watchdog_v2 project and run only Project -> Rebuild Configuration.",
    "Do not run the old pre-rebuild validator because it expects WdTimer : TON.",
    "Do not Transfer, Install, Build and Transfer, or enter Online mode."
)

[System.IO.File]::WriteAllLines(
    $summaryPath,
    $summaryLines,
    [System.Text.UTF8Encoding]::new($false)
)

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
        $relativePath = $_.FullName.Substring(
            $reportRoot.Length
        ).TrimStart("\")

        [PSCustomObject]@{
            RelativePath = $relativePath
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
    Remove-Item `
        -LiteralPath $reportZip `
        -Force
}

Compress-Archive `
    -Path (
        Join-Path $reportRoot "*"
    ) `
    -DestinationPath $reportZip `
    -CompressionLevel Optimal

$reportHash = (
    Get-FileHash `
        -Algorithm SHA256 `
        -LiteralPath $reportZip
).Hash

Write-Title "PATCH COMPLETED"

Write-Host ("Working project: {0}" -f $projectRoot)
Write-Host "TON-less watchdog validation: PASSED"
Write-Host "READY FOR MANUAL REBUILD CONFIGURATION: YES"
Write-Host "READY FOR PLC TRANSFER: NO"
Write-Host ("Report ZIP: {0}" -f $reportZip)
Write-Host ("Report SHA256: {0}" -f $reportHash)
