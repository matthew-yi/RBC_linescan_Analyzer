@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run First Time Setup.bat before launching the analyzer.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" app\rbc_app.py
if errorlevel 1 pause
