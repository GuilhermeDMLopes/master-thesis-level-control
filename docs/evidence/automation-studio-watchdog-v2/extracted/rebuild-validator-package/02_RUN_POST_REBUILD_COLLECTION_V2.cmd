@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "COLLECTOR_SCRIPT=%SCRIPT_DIR%collect_watchdog_after_rebuild_v2.ps1"

echo.
echo Watchdog Post-Rebuild Collector V2
echo ===================================
echo.

echo Checking PowerShell syntax...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($env:COLLECTOR_SCRIPT,[ref]$tokens,[ref]$errors) | Out-Null; if($errors.Count -gt 0){Write-Host 'SYNTAX CHECK FAILED'; $errors | ForEach-Object {Write-Host ($_.Extent.StartLineNumber.ToString() + ': ' + $_.Message)}; exit 1}else{Write-Host 'PowerShell syntax: OK'}"

if errorlevel 1 (
    echo.
    echo Collection was not executed.
    pause
    exit /b 1
)

echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%COLLECTOR_SCRIPT%"

echo.
echo Press any key to close this window.
pause >nul
endlocal
