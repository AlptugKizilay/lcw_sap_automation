@echo off
setlocal enabledelayedexpansion

:: Parametreler
set "ZIP_PATH=%~1"
set "TARGET_DIR=%~2"

if "%ZIP_PATH%"=="" exit /b 1
if "%TARGET_DIR%"=="" exit /b 1

:: 1. Ana uygulamanın tamamen kapanmasını bekle (2 saniye)
timeout /t 2 /nobreak >nul
taskkill /IM LCW_SAP_Automation.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul

:: 2. ZIP paketini hedef klasöre çıkart
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%TARGET_DIR%' -Force"

:: 3. İndirilen geçici ZIP dosyasını temizle
del /f /q "%ZIP_PATH%" >nul 2>&1

:: 4. Güncellenmiş uygulamayı başlat
start "" "%TARGET_DIR%\LCW_SAP_Automation.exe"

exit /b 0
