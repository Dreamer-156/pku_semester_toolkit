@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Python environment is missing. Follow the setup steps in README.md first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo The program stopped with an error. Check the message above.
    pause
    exit /b 1
)
