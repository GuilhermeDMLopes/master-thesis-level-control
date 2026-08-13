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

function Add-Result {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Category,
        [string]$Check,
        [bool]$Passed,
        [string]$Details,
        [bool]$Blocking
    )

    $record = [PSCustomObject]@{
        Category = $Category
        Check = $Check
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
        $Check,
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

function Save-XmlUtf8Bom {
    param(
        [System.Xml.XmlDocument]$Document,
        [string]$Path
    )

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Encoding = New-Object System.Text.UTF8Encoding($true)
    $settings.Indent = $false
    $settings.NewLineHandling = [System.Xml.NewLineHandling]::None

    $writer = [System.Xml.XmlWriter]::Create(
        $Path,
        $settings
    )

    try {
        $Document.Save($writer)
    }
    finally {
        $writer.Dispose()
    }
}

function Get-UniqueFile {
    param(
        [string]$Root,
        [string]$Filter,
        [string]$RequiredText,
        [string]$Description
    )

    $files = @(
        Get-ChildItem `
            -LiteralPath $Root `
            -Recurse `
            -File `
            -Filter $Filter `
            -ErrorAction SilentlyContinue |
        Where-Object {
            if ([string]::IsNullOrWhiteSpace($RequiredText)) {
                $true
            }
            else {
                (Read-AllText -Path $_.FullName).Contains(
                    $RequiredText
                )
            }
        }
    )

    if ($files.Count -ne 1) {
        throw (
            "Expected exactly one {0}. Found {1}." -f
            $Description,
            $files.Count
        )
    }

    return $files[0]
}

function Add-MissingOpcUaVariables {
    param(
        [string]$UadPath,
        [string[]]$RequiredNames
    )

    $document = New-Object System.Xml.XmlDocument
    $document.PreserveWhitespace = $true
    $document.Load($UadPath)

    $taskNodes = @(
        $document.SelectNodes(
            "/OpcUaSource/DefaultView/Module/Task[@Name='Program']"
        )
    )

    if ($taskNodes.Count -ne 1) {
        throw (
            "Expected exactly one DefaultView Task named Program. Found {0}." -f
            $taskNodes.Count
        )
    }

    $taskNode = $taskNodes[0]
    $existingNodes = @(
        $taskNode.SelectNodes("Variable")
    )

    $existingNames = New-Object System.Collections.Generic.List[string]

    foreach ($node in $existingNodes) {
        $name = $node.GetAttribute("Name")

        if (-not [string]::IsNullOrWhiteSpace($name)) {
            $existingNames.Add($name)
        }
    }

    $duplicates = @(
        $existingNames |
        Group-Object |
        Where-Object {
            $_.Count -gt 1
        }
    )

    if ($duplicates.Count -gt 0) {
        $duplicateNames = (
            $duplicates.Name -join ", "
        )

        throw (
            "Duplicate OPC UA variable entries were found: {0}" -f
            $duplicateNames
        )
    }

    $forbiddenPatterns = @(
        "^EnableOut$",
        "^DACOut$",
        "^Wd[A-Za-z0-9_]+$"
    )

    foreach ($name in $existingNames) {
        foreach ($pattern in $forbiddenPatterns) {
            if ($name -match $pattern) {
                throw (
                    "Forbidden OPC UA variable is already published: {0}" -f
                    $name
                )
            }
        }
    }

    $closingWhitespace = $null

    if ($taskNode.LastChild -ne $null) {
        if (
            $taskNode.LastChild.NodeType -eq
            [System.Xml.XmlNodeType]::Whitespace
        ) {
            $closingWhitespace = $taskNode.LastChild
        }
    }

    $addedNames = New-Object System.Collections.Generic.List[string]

    foreach ($requiredName in $RequiredNames) {
        if ($existingNames -contains $requiredName) {
            continue
        }

        $variableNode = $document.CreateElement(
            "Variable"
        )

        $variableNode.SetAttribute(
            "Name",
            $requiredName
        )

        if ($closingWhitespace -ne $null) {
            $indentNode = $document.CreateWhitespace(
                "`r`n        "
            )

            [void]$taskNode.InsertBefore(
                $indentNode,
                $closingWhitespace
            )

            [void]$taskNode.InsertBefore(
                $variableNode,
                $closingWhitespace
            )
        }
        else {
            [void]$taskNode.AppendChild(
                $document.CreateWhitespace(
                    "`r`n        "
                )
            )

            [void]$taskNode.AppendChild(
                $variableNode
            )
        }

        $existingNames.Add($requiredName)
        $addedNames.Add($requiredName)
    }

    Save-XmlUtf8Bom `
        -Document $document `
        -Path $UadPath

    return @($addedNames)
}

function Validate-OpcUaVariables {
    param(
        [string]$UadPath,
        [string[]]$RequiredNames
    )

    $document = New-Object System.Xml.XmlDocument
    $document.PreserveWhitespace = $true
    $document.Load($UadPath)

    $taskNodes = @(
        $document.SelectNodes(
            "/OpcUaSource/DefaultView/Module/Task[@Name='Program']"
        )
    )

    if ($taskNodes.Count -ne 1) {
        throw (
            "OPC UA validation expected one Program task. Found {0}." -f
            $taskNodes.Count
        )
    }

    $names = @(
        $taskNodes[0].SelectNodes("Variable") |
        ForEach-Object {
            $_.GetAttribute("Name")
        }
    )

    $missing = @(
        $RequiredNames |
        Where-Object {
            $names -notcontains $_
        }
    )

    $forbidden = @(
        $names |
        Where-Object {
            ($_ -eq "EnableOut") -or
            ($_ -eq "DACOut") -or
            ($_ -match "^Wd[A-Za-z0-9_]+$")
        }
    )

    $duplicates = @(
        $names |
        Group-Object |
        Where-Object {
            $_.Count -gt 1
        }
    )

    return [PSCustomObject]@{
        Names = $names
        Missing = $missing
        Forbidden = $forbidden
        DuplicateGroups = $duplicates
    }
}

$scriptDirectory = Split-Path `
    -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = $scriptDirectory
}

Write-Title "WATCHDOG OPC UA FINALIZER"

Write-Host "This script modifies only the watchdog_v2 working copy."
Write-Host "It does not connect to the PLC, build, transfer, install, or enter Online mode."
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
    throw "Close Automation Studio before running the finalizer."
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
        "WatchdogOpcUaFinalizeReport-" +
        $runId
    )

$reportZip = $reportRoot + ".zip"
$summaryPath = Join-Path $reportRoot "00-summary.txt"
$checksPath = Join-Path $reportRoot "01-checks.csv"
$opcUaListPath = Join-Path $reportRoot "02-opcua-variable-list.txt"
$taskInfoPath = Join-Path $reportRoot "03-task-information.txt"
$manifestPath = Join-Path $reportRoot "04-manifest-sha256.csv"
$beforeDirectory = Join-Path $reportRoot "before"
$afterDirectory = Join-Path $reportRoot "after"
$contextPath = Join-Path $scriptDirectory "watchdog-finalizer-context.json"

New-Item `
    -ItemType Directory `
    -Path $reportRoot `
    -Force |
    Out-Null

New-Item `
    -ItemType Directory `
    -Path $beforeDirectory `
    -Force |
    Out-Null

New-Item `
    -ItemType Directory `
    -Path $afterDirectory `
    -Force |
    Out-Null

$results = New-Object System.Collections.ArrayList

Write-Title "LOCATING PROJECT FILES"

$apjFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.apj" `
    -RequiredText "" `
    -Description ".apj project file"

$variableFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.var" `
    -RequiredText "MASTER_THESIS_WATCHDOG_V2_VARIABLES" `
    -Description "watchdog variable file"

$initFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -RequiredText "MASTER_THESIS_WATCHDOG_V2_INIT" `
    -Description "watchdog INIT file"

$cyclicFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -RequiredText "MASTER_THESIS_WATCHDOG_V2_CYCLIC" `
    -Description "watchdog CYCLIC file"

$exitFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.st" `
    -RequiredText "MASTER_THESIS_WATCHDOG_V2_EXIT" `
    -Description "watchdog EXIT file"

$ioMapFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "IoMap.iom" `
    -RequiredText "::Program:DACOut" `
    -Description "patched IoMap.iom"

$uadFile = Get-UniqueFile `
    -Root $projectRoot `
    -Filter "*.uad" `
    -RequiredText "<OpcUaSource" `
    -Description "OPC UA Default View file"

Write-Host ("Project:   {0}" -f $apjFile.FullName)
Write-Host ("Variables: {0}" -f $variableFile.FullName)
Write-Host ("INIT:      {0}" -f $initFile.FullName)
Write-Host ("CYCLIC:    {0}" -f $cyclicFile.FullName)
Write-Host ("EXIT:      {0}" -f $exitFile.FullName)
Write-Host ("I/O map:   {0}" -f $ioMapFile.FullName)
Write-Host ("OPC UA:    {0}" -f $uadFile.FullName)

Write-Title "BACKING UP OPC UA DEFAULT VIEW"

$uadBackupPath = (
    $uadFile.FullName +
    ".pre_finalizer_" +
    $runId +
    ".bak"
)

Copy-Item `
    -LiteralPath $uadFile.FullName `
    -Destination $uadBackupPath `
    -Force

Copy-Item `
    -LiteralPath $uadFile.FullName `
    -Destination (
        Join-Path $beforeDirectory "OpcUaMap-before.uad"
    ) `
    -Force

Add-Result `
    -Results $results `
    -Category "Backup" `
    -Check "OPC UA backup created" `
    -Passed (
        Test-Path `
            -LiteralPath $uadBackupPath `
            -PathType Leaf
    ) `
    -Details $uadBackupPath `
    -Blocking $true

Write-Title "VALIDATING CORE WATCHDOG PROJECT"

$variableText = Read-AllText `
    -Path $variableFile.FullName

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

    Add-Result `
        -Results $results `
        -Category "Variables" `
        -Check $declaration.Name `
        -Passed $present `
        -Details $variableFile.FullName `
        -Blocking $true
}

$initText = Read-AllText -Path $initFile.FullName
$cyclicText = Read-AllText -Path $cyclicFile.FullName
$exitText = Read-AllText -Path $exitFile.FullName
$ioMapText = Read-AllText -Path $ioMapFile.FullName

$coreChecks = @(
    [PSCustomObject]@{
        Category = "Logic"
        Name = "INIT safe Enable"
        Text = $initText
        Pattern = "Enable\s*:=\s*FALSE\s*;"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "INIT safe DAC"
        Text = $initText
        Pattern = "DAC\s*:=\s*0\s*;"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "CYCLIC one-second timeout"
        Text = $cyclicText
        Pattern = "PT\s*:=\s*T#1s"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "CYCLIC output gate Enable"
        Text = $cyclicText
        Pattern = "EnableOut\s*:=\s*AppliedEnable\s*;"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "CYCLIC output gate DAC"
        Text = $cyclicText
        Pattern = "DACOut\s*:=\s*AppliedDAC\s*;"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "EXIT safe Enable"
        Text = $exitText
        Pattern = "EnableOut\s*:=\s*FALSE\s*;"
    },
    [PSCustomObject]@{
        Category = "Logic"
        Name = "EXIT safe DAC"
        Text = $exitText
        Pattern = "DACOut\s*:=\s*0\s*;"
    },
    [PSCustomObject]@{
        Category = "I/O Mapping"
        Name = "Nivel mapped to physical input"
        Text = $ioMapText
        Pattern = "::Program:Nivel"
    },
    [PSCustomObject]@{
        Category = "I/O Mapping"
        Name = "DACOut mapped to physical output"
        Text = $ioMapText
        Pattern = "::Program:DACOut"
    },
    [PSCustomObject]@{
        Category = "I/O Mapping"
        Name = "EnableOut mapped to physical output"
        Text = $ioMapText
        Pattern = "::Program:EnableOut"
    }
)

foreach ($coreCheck in $coreChecks) {
    $present = Test-Regex `
        -Text $coreCheck.Text `
        -Pattern $coreCheck.Pattern

    Add-Result `
        -Results $results `
        -Category $coreCheck.Category `
        -Check $coreCheck.Name `
        -Passed $present `
        -Details $coreCheck.Pattern `
        -Blocking $true
}

$oldEnableMapping = [regex]::IsMatch(
    $ioMapText,
    "::Program:Enable(?![A-Za-z0-9_])"
)

$oldDacMapping = [regex]::IsMatch(
    $ioMapText,
    "::Program:DAC(?![A-Za-z0-9_])"
)

Add-Result `
    -Results $results `
    -Category "I/O Mapping" `
    -Check "Old direct Enable mapping removed" `
    -Passed (-not $oldEnableMapping) `
    -Details $ioMapFile.FullName `
    -Blocking $true

Add-Result `
    -Results $results `
    -Category "I/O Mapping" `
    -Check "Old direct DAC mapping removed" `
    -Passed (-not $oldDacMapping) `
    -Details $ioMapFile.FullName `
    -Blocking $true

$prePatchFailures = @(
    $results |
    Where-Object {
        $_.Blocking -and (-not $_.Passed)
    }
)

if ($prePatchFailures.Count -gt 0) {
    throw (
        "Core watchdog validation failed before OPC UA modification. Failure count: {0}" -f
        $prePatchFailures.Count
    )
}

Write-Title "ADDING MISSING OPC UA VARIABLES"

$requiredOpcUaVariables = @(
    "Nivel",
    "DAC",
    "Enable",
    "Heartbeat",
    "SafetyReset",
    "WatchdogHealthy",
    "WatchdogTripped",
    "AppliedEnable",
    "AppliedDAC"
)

$addedVariables = @(
    Add-MissingOpcUaVariables `
        -UadPath $uadFile.FullName `
        -RequiredNames $requiredOpcUaVariables
)

if ($addedVariables.Count -eq 0) {
    Write-Host "No OPC UA variables needed to be added."
}
else {
    Write-Host (
        "Added OPC UA variables: {0}" -f
        ($addedVariables -join ", ")
    )
}

$opcUaValidation = Validate-OpcUaVariables `
    -UadPath $uadFile.FullName `
    -RequiredNames $requiredOpcUaVariables

Add-Result `
    -Results $results `
    -Category "OPC UA" `
    -Check "All required variables published" `
    -Passed ($opcUaValidation.Missing.Count -eq 0) `
    -Details (
        "Missing: {0}" -f
        ($opcUaValidation.Missing -join ", ")
    ) `
    -Blocking $true

Add-Result `
    -Results $results `
    -Category "OPC UA" `
    -Check "No physical output variables published" `
    -Passed ($opcUaValidation.Forbidden.Count -eq 0) `
    -Details (
        "Forbidden: {0}" -f
        ($opcUaValidation.Forbidden -join ", ")
    ) `
    -Blocking $true

Add-Result `
    -Results $results `
    -Category "OPC UA" `
    -Check "No duplicate variable entries" `
    -Passed ($opcUaValidation.DuplicateGroups.Count -eq 0) `
    -Details (
        "Duplicate groups: {0}" -f
        $opcUaValidation.DuplicateGroups.Count
    ) `
    -Blocking $true

Copy-Item `
    -LiteralPath $uadFile.FullName `
    -Destination (
        Join-Path $afterDirectory "OpcUaMap-after.uad"
    ) `
    -Force

[System.IO.File]::WriteAllLines(
    $opcUaListPath,
    @($opcUaValidation.Names),
    [System.Text.UTF8Encoding]::new($false)
)

Write-Title "COLLECTING TASK INFORMATION"

$taskLines = New-Object System.Collections.Generic.List[string]

$compiledIoMapFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "iomap.xml" `
        -ErrorAction SilentlyContinue
)

$detectedTaskClasses = New-Object System.Collections.Generic.List[int]

foreach ($compiledFile in $compiledIoMapFiles) {
    $compiledText = Read-AllText `
        -Path $compiledFile.FullName

    $matches = @(
        [regex]::Matches(
            $compiledText,
            'Device="TC#(?<Class>[0-9]+)-CPYDEV"\s+DPName="::Program:[A-Za-z0-9_]+"'
        )
    )

    foreach ($match in $matches) {
        $classNumber = [int]$match.Groups["Class"].Value

        if (-not ($detectedTaskClasses -contains $classNumber)) {
            $detectedTaskClasses.Add($classNumber)
        }
    }
}

$hardwareFiles = @(
    Get-ChildItem `
        -LiteralPath $projectRoot `
        -Recurse `
        -File `
        -Filter "Hardware.hw" `
        -ErrorAction SilentlyContinue
)

$taskLines.Add(
    "Detected Program task classes from compiled I/O map: " +
    ($detectedTaskClasses -join ", ")
)

foreach ($hardwareFile in $hardwareFiles) {
    $hardwareText = Read-AllText `
        -Path $hardwareFile.FullName

    $taskLines.Add("")
    $taskLines.Add("Hardware file: " + $hardwareFile.FullName)

    foreach ($classNumber in $detectedTaskClasses) {
        $durationPattern = (
            'ID="Cyclic' +
            $classNumber +
            'Duration"\s+Value="(?<Value>[0-9]+)"'
        )

        $tolerancePattern = (
            'ID="Cyclic' +
            $classNumber +
            'Tolerance"\s+Value="(?<Value>[0-9]+)"'
        )

        $durationMatch = [regex]::Match(
            $hardwareText,
            $durationPattern
        )

        $toleranceMatch = [regex]::Match(
            $hardwareText,
            $tolerancePattern
        )

        if ($durationMatch.Success) {
            $durationRaw = [int64]$durationMatch.Groups["Value"].Value
            $durationMs = $durationRaw / 1000.0

            $taskLines.Add(
                (
                    "Cyclic{0} duration raw={1}; derived={2} ms" -f
                    $classNumber,
                    $durationRaw,
                    $durationMs
                )
            )
        }

        if ($toleranceMatch.Success) {
            $toleranceRaw = [int64]$toleranceMatch.Groups["Value"].Value
            $toleranceMs = $toleranceRaw / 1000.0

            $taskLines.Add(
                (
                    "Cyclic{0} tolerance raw={1}; derived={2} ms" -f
                    $classNumber,
                    $toleranceRaw,
                    $toleranceMs
                )
            )
        }
    }
}

[System.IO.File]::WriteAllLines(
    $taskInfoPath,
    $taskLines,
    [System.Text.UTF8Encoding]::new($false)
)

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
Write-Host "The OPC UA variables were added using the same Variable-entry format already used by the project."
Write-Host "Do not transfer anything to the PLC."

$summaryLines = @(
    "WATCHDOG OPC UA FINALIZER",
    "=========================",
    "",
    ("Generated at: {0}" -f (Get-Date).ToString("o")),
    ("Working project: {0}" -f $projectRoot),
    ("Project file: {0}" -f $apjFile.FullName),
    ("OPC UA file: {0}" -f $uadFile.FullName),
    ("OPC UA backup: {0}" -f $uadBackupPath),
    ("Added variables: {0}" -f ($addedVariables -join ", ")),
    ("Static project validation: {0}" -f $staticStatus),
    ("Ready for manual Rebuild Configuration: {0}" -f $readyForRebuild),
    "Ready for PLC transfer: NO",
    "",
    "Next action when validation is PASSED:",
    "Open the watchdog_v2 project and run only Project -> Rebuild Configuration.",
    "Do not Transfer, Install, Build and Transfer, or enter Online mode.",
    "",
    "Access-right note:",
    "The project UAD file uses simple Variable entries without per-variable ACL attributes.",
    "This script preserves that existing format.",
    "Heartbeat and SafetyReset must be writable.",
    "The diagnostic variables are overwritten by the PLC cyclic logic and do not bypass the physical-output gate."
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
    ProjectFile = $apjFile.FullName
    UadFile = $uadFile.FullName
    ValidationTime = (Get-Date).ToString("o")
    ValidationPassed = $validationPassed
    ReadyForManualRebuild = $validationPassed
    ReportZip = $reportZip
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

Write-Host ""
Write-Host ("Report ZIP: {0}" -f $reportZip)
Write-Host ("Report SHA256: {0}" -f $reportHash)

if (-not $validationPassed) {
    exit 2
}

$openAnswer = Read-Host "Open the validated watchdog project in Automation Studio now? Type YES or NO"

if ($openAnswer -eq "YES") {
    $automationStudioCandidates = @(
        "C:\BrAutomation\AS410\Bin-en\AutomationStudio.exe",
        "C:\BrAutomation\AS410\Bin-de\AutomationStudio.exe"
    )

    $automationStudioExe = $null

    foreach ($candidate in $automationStudioCandidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $automationStudioExe = $candidate
            break
        }
    }

    if ($automationStudioExe -eq $null) {
        Write-Host "AutomationStudio.exe was not found at the expected AS4.10 paths."
        Write-Host ("Open this project manually: {0}" -f $apjFile.FullName)
    }
    else {
        Start-Process `
            -FilePath $automationStudioExe `
            -ArgumentList @($apjFile.FullName)

        Write-Host "Automation Studio started."
        Write-Host "Run only Project -> Rebuild Configuration."
    }
}
