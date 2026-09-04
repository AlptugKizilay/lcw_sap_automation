@echo off
setlocal enabledelayedexpansion

set ZIP_PATH=%~1
set TARGET_DIR=%~2

:WAIT_LOOP
tasklist /FI "IMAGENAME eq LCW_SAP_Automation.exe" 2>NUL | find /I /N "LCW_SAP_Automation.exe">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

timeout /t 2 /nobreak >nul

tar -xf "%ZIP_PATH%" -C "%TARGET_DIR%"

if exist "%ZIP_PATH%" (
    del /f /q "%ZIP_PATH%"
)

cd /d "%TARGET_DIR%"
if exist "LCW_SAP_Automation.exe" (
    explorer.exe "%TARGET_DIR%\LCW_SAP_Automation.exe"
)

exit
