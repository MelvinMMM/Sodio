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
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
echo ====================================================
echo   Sodio [Sonic-Audio] a ete arrete avec succes.
echo ====================================================
ping 127.0.0.1 -n 2 >nul
