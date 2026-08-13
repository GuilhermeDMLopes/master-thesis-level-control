@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "VALIDATOR_SCRIPT=%SCRIPT_DIR%validate_watchdog_before_rebuild_v2.ps1"

echo.
echo Watchdog Pre-Rebuild Validator V2
echo ==================================
echo.
echo Read-only project validation.
echo.

echo Checking PowerShell syntax...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($env:VALIDATOR_SCRIPT,[ref]$tokens,[ref]$errors) | Out-Null; if($errors.Count -gt 0){Write-Host 'SYNTAX CHECK FAILED'; $errors | ForEach-Object {Write-Host ($_.Extent.StartLineNumber.ToString() + ': ' + $_.Message)}; exit 1}else{Write-Host 'PowerShell syntax: OK'}"

if errorlevel 1 (
    echo.
    echo Validation was not executed.
    echo No project file was modified.
    pause
    exit /b 1
)

echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%VALIDATOR_SCRIPT%"

echo.
echo Press any key to close this window.
pause >nul
endlocal
