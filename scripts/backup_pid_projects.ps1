[CmdletBinding()]
param([string]$Repository = 'C:\Projetos\master-thesis-level-control')
$ErrorActionPreference = 'Stop'
$destination = Join-Path $env:USERPROFILE ('Documents\4diac-backups\' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-basic-pid')
if (Test-Path -LiteralPath $destination) { throw 'Backup destination already exists.' }
$source = Join-Path $Repository '4diac\application\PID_Identification_Observer'
if (-not (Test-Path -LiteralPath $source)) { throw "Project missing: $source" }
New-Item -ItemType Directory -Path $destination | Out-Null
foreach ($name in @('PID_Identification_Observer', 'PID_Basic_Adaptive')) {
    $project = Join-Path $Repository "4diac\application\$name"
    if (Test-Path -LiteralPath $project) {
        Copy-Item -LiteralPath $project -Destination $destination -Recurse -Force
        foreach ($file in Get-ChildItem -LiteralPath $project -Recurse -File -Force) {
            $relative = $file.FullName.Substring($project.Length).TrimStart('\')
            $copy = Join-Path (Join-Path $destination $name) $relative
            if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $copy).Hash) {
                throw "Backup mismatch: $relative"
            }
        }
    }
}
& git -C $Repository rev-parse HEAD | Set-Content (Join-Path $destination 'commit.txt')
if ($LASTEXITCODE -ne 0) { throw 'Cannot record commit.' }
& git -C $Repository status --short | Set-Content (Join-Path $destination 'git-status.txt')
if ($LASTEXITCODE -ne 0) { throw 'Cannot record status.' }
'Files only: runtime state, exported C++ and FORTE executable are not included. Save IDE changes before backup.' |
    Set-Content (Join-Path $destination 'README.txt')
Write-Host "Verified backup: $destination" -ForegroundColor Green
