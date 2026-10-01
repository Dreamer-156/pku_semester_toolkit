@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Python environment is missing. Follow the setup steps in README.md first.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Drag a .tex file onto build-homework.cmd to make a PDF.
    echo Or run: build-homework.cmd "path\to\homework.tex"
    pause
    exit /b 2
)

".venv\Scripts\python.exe" scripts\build_latex.py "%~1"
set "result=%errorlevel%"
if not "%result%"=="0" echo Build failed. Read the message above.
echo Press any key to close this window.
pause >nul
exit /b %result%
