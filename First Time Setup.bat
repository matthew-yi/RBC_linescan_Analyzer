@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 app\install_rbc.py
) else (
    python app\install_rbc.py
)
if errorlevel 1 echo Setup failed. Python 3.10+ must be installed from https://www.python.org/downloads/
pause
