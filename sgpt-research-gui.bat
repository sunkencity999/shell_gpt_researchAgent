@echo off
REM Windows launcher for Shell GPT Research Agent GUI

setlocal
set "SCRIPT_DIR=%~dp0"
set "VENV_PATH=%SCRIPT_DIR%venv\Scripts"
set "PYTHONPATH=%SCRIPT_DIR%"

REM Check if venv exists
if not exist "%VENV_PATH%\python.exe" (
    echo [ERROR] Python venv not found! Please run install_windows.bat first.
    pause
    exit /b 1
)

REM Change to script directory
pushd "%SCRIPT_DIR%"

REM Load .env variables if present (simplified for Windows)
if exist "%SCRIPT_DIR%.env" (
    echo [INFO] Loading environment variables from .env file
)

REM Launch GUI
echo [INFO] Launching Shell GPT Research Agent GUI...
"%VENV_PATH%\python.exe" sgptAgent\gui_app.py %*

REM Check for errors
if errorlevel 1 (
    echo [ERROR] The application failed to launch. Ensure all dependencies are installed.
    pause
)

popd
endlocal
