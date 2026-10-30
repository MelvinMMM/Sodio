@echo off
title Arret de Sodio
cd /d "%~dp0"
set STOPPED=0
if exist sodio.pid (
    set /p PID=<sodio.pid
    taskkill /F /PID %PID% >nul 2>&1
    del sodio.pid >nul 2>&1
    set STOPPED=1
)
if exist phoenix_voice.pid (
    set /p PID=<phoenix_voice.pid
    taskkill /F /PID %PID% >nul 2>&1
    del phoenix_voice.pid >nul 2>&1
    set STOPPED=1
)
if %STOPPED%==1 (
    echo ====================================================
    echo   Sodio (Sonic-Audio) a ete arrete avec succes.
    echo ====================================================
) else (
    echo Sodio n'etait pas en cours d'execution.
)
ping 127.0.0.1 -n 2 >nul
