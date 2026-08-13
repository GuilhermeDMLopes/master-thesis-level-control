[CmdletBinding()]
param(
    [string]$ContextPath = "",
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

if ([string]::IsNullOrWhiteSpace($ContextPath)) {
    $ContextPath = Join-Path `
        $scriptDirectory `
        "rebuild-validation-context-v2.json"
}

Write-Title "WATCHDOG POST-REBUILD COLLECTOR V2"

if (-not (Test-Path -LiteralPath $ContextPath -PathType Leaf)) {
    throw (
        "Validation context not found: {0}" -f
        $ContextPath
    )
}

$context = Get-Content `
    -LiteralPath $ContextPath `
    -Raw |
    ConvertFrom-Json

if (-not $context.ValidationPassed) {
    throw "The pre-rebuild validation did not pass."
}

$projectRoot = $context.WorkingProjectRoot

if (-not (Test-Path -LiteralPath $projectRoot -PathType Container)) {
    throw (
        "Working project not found: {0}" -f
        $projectRoot
    )
}

$validationTime = [datetime]::Parse($context.ValidationTime)
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$reportRoot = Join-Path $OutputRoot ("WatchdogPostRebuildCollectionV2-" + $runId)
$reportZip = $reportRoot + ".zip"
$summaryPath = Join-Path $reportRoot "00-summary.txt"
$recentFilesPath = Join-Path $reportRoot "01-recent-files.csv"
$matchesPath = Join-Path $reportRoot "02-error-warning-matches.txt"
$manifestPath = Join-Path $reportRoot "03-manifest-sha256.csv"

New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null

$completed = Read-Host "Did Rebuild Configuration finish? Type YES or NO"
$errorCount = Read-Host "Errors displayed by Automation Studio"
$warningCount = Read-Host "Warnings displayed by Automation Studio"
$resultText = Read-Host "Final Build result/status text"

$recentFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LastWriteTime -ge $validationTime.AddMinutes(-1)
    } |
    Sort-Object LastWriteTime
)

$recentFiles |
    ForEach-Object {
        [PSCustomObject]@{
            RelativePath = Get-RelativePath `
                -BasePath $projectRoot `
                -FullPath $_.FullName
            Length = $_.Length
            LastWriteTime = $_.LastWriteTime.ToString("o")
        }
    } |
    Export-Csv `
        -LiteralPath $recentFilesPath `
        -NoTypeInformation `
        -Encoding UTF8

$issueLines = New-Object System.Collections.Generic.List[string]

foreach ($file in $recentFiles) {
    if ($file.Length -le 10MB) {
        $matches = @(
            Select-String `
                -LiteralPath $file.FullName `
                -Pattern @(
                    "error",
                    "warning",
                    "fatal",
                    "failed"
                ) `
                -CaseSensitive:$false `
                -Context 1,2 `
                -ErrorAction SilentlyContinue
        )

        foreach ($match in $matches) {
            $issueLines.Add("")
            $issueLines.Add(
                (
                    "{0}:{1} | {2}" -f
                    $match.Path,
                    $match.LineNumber,
                    $match.Pattern
                )
            )

            foreach ($line in $match.Context.PreContext) {
                $issueLines.Add("  BEFORE | " + $line)
            }

            $issueLines.Add("  MATCH  | " + $match.Line)

            foreach ($line in $match.Context.PostContext) {
                $issueLines.Add("  AFTER  | " + $line)
            }
        }
    }
}

[System.IO.File]::WriteAllLines(
    $matchesPath,
    $issueLines,
    [System.Text.UTF8Encoding]::new($false)
)

$summaryLines = @(
    "WATCHDOG POST-REBUILD COLLECTION V2",
    "===================================",
    "",
    ("Generated at: {0}" -f (Get-Date).ToString("o")),
    ("Working project: {0}" -f $projectRoot),
    ("Rebuild completed according to operator: {0}" -f $completed),
    ("Errors displayed: {0}" -f $errorCount),
    ("Warnings displayed: {0}" -f $warningCount),
    ("Final result text: {0}" -f $resultText),
    ("Recent files found: {0}" -f $recentFiles.Count),
    ("Automated issue-context lines: {0}" -f $issueLines.Count),
    "",
    "Ready for PLC transfer: NO"
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
Write-Host "Do not transfer the project to the PLC."
