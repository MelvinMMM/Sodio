@echo off
title Installation au demarrage de Windows - Sodio
cd /d "%~dp0"

set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\Sodio.lnk"
set "OLD_SHORTCUT=%TARGET_DIR%\PhoenixVoice.lnk"
set "SCRIPT_PATH=%~dp0lancer_silencieux.vbs"

if exist "%OLD_SHORTCUT%" del "%OLD_SHORTCUT%" >nul 2>&1

echo Creation du raccourci dans le dossier Demarrage...
powershell -Command "$s = (New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo ====================================================
    echo   SUCCES ! Sodio (Sonic-Audio) demarrera
    echo   automatiquement a chaque allumage de votre PC.
    echo ====================================================
) else (
    echo Erreur lors de la creation du raccourci.
)
pause
