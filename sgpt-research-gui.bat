@echo off
REM Windows launcher for Shell GPT Research Agent GUI
REM Ensure you are in the project root directory

setlocal
set "VENV_PATH=%~dp0venv\Scripts"
set "PYTHONPATH=%~dp0sgptAgent"

if exist "%VENV_PATH%\python.exe" (
    pushd "%~dp0"
    "%VENV_PATH%\python.exe" -m sgptAgent.gui_app %*
    if errorlevel 1 (
        echo [ERROR] The application failed to launch. Ensure all dependencies are installed with install_windows.bat.
    )
    popd
) else (
    echo [ERROR] Python venv not found! Please run install_windows.bat or set up the venv first.
    exit /b 1
)
endlocal
