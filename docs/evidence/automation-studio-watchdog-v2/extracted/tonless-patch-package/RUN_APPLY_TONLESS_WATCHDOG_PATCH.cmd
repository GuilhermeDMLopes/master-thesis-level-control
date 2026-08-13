@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PATCH_SCRIPT=%SCRIPT_DIR%apply_tonless_watchdog_patch.ps1"

echo.
echo TON-less Watchdog Patch
echo =======================
echo.
echo This tool modifies only the watchdog_v2 working copy.
echo It does not connect to, build for, transfer to, or write to the PLC.
echo.
echo Close Automation Studio before continuing.
echo.

echo Checking PowerShell syntax...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($env:PATCH_SCRIPT,[ref]$tokens,[ref]$errors) | Out-Null; if($errors.Count -gt 0){Write-Host 'SYNTAX CHECK FAILED'; $errors | ForEach-Object {Write-Host ($_.Extent.StartLineNumber.ToString() + ': ' + $_.Message)}; exit 1}else{Write-Host 'PowerShell syntax: OK'}"

if errorlevel 1 (
    echo.
    echo Patch was not executed.
    echo No project file was modified.
    pause
    exit /b 1
)

echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PATCH_SCRIPT%"

echo.
echo Press any key to close this window.
pause >nul
endlocal
