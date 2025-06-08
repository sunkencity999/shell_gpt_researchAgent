@echo off
REM Windows launcher for Shell GPT Research Agent GUI
REM Ensure you are in the project root directory

setlocal
set "VENV_PATH=%~dp0venv\Scripts"
set "PYTHONPATH=%~dp0sgptAgent"

if exist "%VENV_PATH%\python.exe" (
    "%VENV_PATH%\python.exe" %~dp0sgptAgent\gui_app.py %*
) else (
    echo [ERROR] Python venv not found! Please run install.sh or set up the venv first.
    exit /b 1
)
endlocal
