@echo off
title Desinstallation du demarrage de Windows - Sodio
cd /d "%~dp0"

set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\Sodio.lnk"
set "OLD_SHORTCUT=%TARGET_DIR%\PhoenixVoice.lnk"

set REMOVED=0
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%" >nul 2>&1
    set REMOVED=1
)
if exist "%OLD_SHORTCUT%" (
    del "%OLD_SHORTCUT%" >nul 2>&1
    set REMOVED=1
)

if %REMOVED%==1 (
    echo ====================================================
    echo   Sodio a ete retire du demarrage de Windows.
    echo ====================================================
) else (
    echo Sodio n'etait pas configure au demarrage.
)
pause
