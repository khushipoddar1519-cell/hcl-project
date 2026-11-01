@echo off
set DIR=%~dp0
cd /d "%DIR%"

if exist "%DIR%.venv\Scripts\python.exe" (
    set PY="%DIR%.venv\Scripts\python.exe"
) else (
    set PY=python
)

echo Starting Hotel Analytics Suite...
%PY% start.py %*
pause
