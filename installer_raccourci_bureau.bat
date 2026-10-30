@echo off
title Installation du raccourci Bureau - Sodio
cd /d "%~dp0"

echo ====================================================
echo   Creation du raccourci Sodio sur le Bureau...
echo ====================================================

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Desktop = [Environment]::GetFolderPath('Desktop'); $ShortcutPath = Join-Path $Desktop 'Sodio.lnk'; $Shortcut = $WshShell.CreateShortcut($ShortcutPath); $Shortcut.TargetPath = 'C:\Users\melvi\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe'; $Shortcut.Arguments = 'python\gui_app.py'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0assets\icon.ico, 0'; $Shortcut.Description = 'Sodio (Sonic-Audio) - Micro-agent de Dictee Vocale de Melvin'; $Shortcut.Save()"

if exist "%USERPROFILE%\Desktop\Sodio.lnk" (
    echo ====================================================
    echo   SUCCES ! L'icone Sodio est presente sur votre Bureau.
    echo   Double-cliquez dessus pour ouvrir l'interface.
    echo ====================================================
) else (
    echo Erreur lors de la creation du raccourci.
)
pause
