[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Projetos\master-thesis-level-control"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RequiredBranch = "feature/mpc-preparation"
$RequiredContractTag = "mpc-local-deadzone-revised-execution-semantics"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $ProjectRoot "scripts\local_deadzone_resume_11650_11900.py"
$GatewayScript = Join-Path $ProjectRoot "gateway\src\gateway_opcua.py"

function Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 100)
    Write-Host $Title
    Write-Host ("=" * 100)
}

function Stop-TrackedProcess {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$Label
    )

    if ($null -eq $Process) {
        return
    }

    try {
        $Process.Refresh()
        if (-not $Process.HasExited) {
            Write-Host "Stopping $Label PID $($Process.Id)..."
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $Process.Id -Timeout 10 -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Host "Cleanup warning for $Label`: $($_.Exception.Message)"
    }
}

Set-Location $ProjectRoot

Section "PROTECTED LOCAL DEAD-ZONE RESUME - 11650..11900"

Write-Host "REAL-LAB EXECUTOR: YES"
Write-Host "REAL ACTUATION: YES, only after explicit operator confirmation"
Write-Host "FORTE / PI / MPC: MUST REMAIN STOPPED"
Write-Host "POINTS: 11650, 11700, 11750, 11800, 11850, 11900"
Write-Host "11600 REPEAT: NO"
Write-Host ""
Write-Host "DO NOT RUN THIS WRAPPER WITHOUT PHYSICAL ACCESS TO THE PLANT."

$Branch = (git branch --show-current).Trim()
if ($Branch -ne $RequiredBranch) {
    throw "Expected branch $RequiredBranch, found $Branch"
}

if (@(git status --porcelain).Count -ne 0) {
    git status --short
    throw "Repository must be clean before real execution."
}

$TagHead = (git rev-list -n 1 $RequiredContractTag 2>$null)
if ([string]::IsNullOrWhiteSpace($TagHead)) {
    throw "Required revised-execution contract tag missing."
}

$HeadFull = (git rev-parse HEAD).Trim()
$IsAncestor = $false
git merge-base --is-ancestor $RequiredContractTag HEAD
if ($LASTEXITCODE -eq 0) {
    $IsAncestor = $true
}

if (-not $IsAncestor) {
    throw "Current HEAD does not contain the revised-execution contract tag."
}

if (@(Get-Process forte -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "FORTE is running. Stop FORTE before this open-loop identification."
}

if (@(
    Get-NetTCPConnection -State Listen -LocalPort 61499 -ErrorAction SilentlyContinue
).Count -ne 0) {
    throw "FORTE management port 61499 is occupied."
}

foreach ($Path in @($Python,$Runner,$GatewayScript)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file missing: $Path"
    }
}

Section "PHYSICAL SAFETY CONFIRMATION"

Write-Host "Confirm physically:"
Write-Host "  physical/emergency stop is immediately accessible"
Write-Host "  tank is visually safe"
Write-Host "  current physical level is <=1 cm before the first point"
Write-Host "  ruler/reference is visible"
Write-Host "  FORTE/PI/MPC are not controlling the plant"
Write-Host "  you will press Q or use the physical stop for any concern"
Write-Host ""
Write-Host "Active abort remains 1100 raw / 5 cm."

$Token = Read-Host "Digite LOCAL_DEADZONE_RESUME_PHYSICAL_READY somente se todos os itens forem verdadeiros"
if ($Token -ne "LOCAL_DEADZONE_RESUME_PHYSICAL_READY") {
    throw "Physical safety confirmation not provided."
}

Section "VERIFY PLC CONNECTIVITY"

$Plc = Test-NetConnection 10.0.0.3 -Port 4840 -WarningAction SilentlyContinue
Write-Host "PLC 10.0.0.3:4840 reachable: $($Plc.TcpTestSucceeded)"

if (-not $Plc.TcpTestSucceeded) {
    throw "PLC OPC UA endpoint unavailable."
}

$gateway = $null
$GatewayStartedHere = $false

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$EvidenceDir = Join-Path $ProjectRoot "data\raw\local-deadzone-resume-$Stamp"
$GatewayOut = Join-Path $EvidenceDir "gateway.out.log"
$GatewayErr = Join-Path $EvidenceDir "gateway.err.log"

try {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

    Section "START OR VERIFY CANONICAL GATEWAY"

    $Listeners = @(
        Get-NetTCPConnection -State Listen -LocalPort 4841 -ErrorAction SilentlyContinue
    )

    if ($Listeners.Count -gt 1) {
        throw "Multiple listeners found on gateway port 4841."
    }

    if ($Listeners.Count -eq 1) {
        $GatewayPid = $Listeners[0].OwningProcess
        $GatewayInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$GatewayPid" -ErrorAction SilentlyContinue

        if (
            $null -eq $GatewayInfo -or
            [string]::IsNullOrWhiteSpace($GatewayInfo.CommandLine) -or
            -not $GatewayInfo.CommandLine.Contains("gateway_opcua.py")
        ) {
            throw "Port 4841 is occupied by a non-canonical process."
        }

        Write-Host "Existing canonical gateway PID: $GatewayPid"
    }
    else {
        $gateway = Start-Process `
            -FilePath $Python `
            -ArgumentList @($GatewayScript) `
            -WorkingDirectory $ProjectRoot `
            -RedirectStandardOutput $GatewayOut `
            -RedirectStandardError $GatewayErr `
            -PassThru

        $GatewayStartedHere = $true
        Start-Sleep -Seconds 4

        $gateway.Refresh()
        if ($gateway.HasExited) {
            throw "Gateway exited during startup."
        }

        $Owned = @(
            Get-NetTCPConnection -State Listen -LocalPort 4841 -ErrorAction SilentlyContinue |
            Where-Object { $_.OwningProcess -eq $gateway.Id }
        )

        if ($Owned.Count -eq 0) {
            throw "Started gateway does not own port 4841."
        }

        Write-Host "Gateway PID: $($gateway.Id)"
    }

    Section "RUN PROTECTED RESUME EXECUTOR"

    & $Python $Runner --run --evidence-dir $EvidenceDir
    $RunExit = $LASTEXITCODE

    if ($RunExit -ne 0) {
        throw "Protected resume executor failed or aborted."
    }

    Write-Host ""
    Write-Host "Executor returned success."
    Write-Host "Evidence directory:"
    Write-Host $EvidenceDir
    Write-Host ""
    Write-Host "DO NOT automatically repeat any partial/aborted point."
}
finally {
    if ($GatewayStartedHere) {
        Stop-TrackedProcess -Process $gateway -Label "gateway"
    }
}
