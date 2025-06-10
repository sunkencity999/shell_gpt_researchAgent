@echo off
setlocal enabledelayedexpansion

REM Shell GPT Research Agent - Windows Installer
echo --- Shell GPT Research Agent Installer ---
echo.

REM ===============================================
REM 1. Check for Python installation
REM ===============================================
echo [1/8] Checking for Python installation...
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python3"
    ) else (
        echo [ERROR] Python is not installed or not found in your PATH.
        echo Please install Python 3.8 or newer and add it to your PATH, then re-run this installer.
        pause
        exit /b 1
    )
)
echo Found Python: %PYTHON_CMD%

REM ===============================================
REM 2. Create a virtual environment
REM ===============================================
if not exist venv (
    echo [2/8] Creating virtual environment...
    %PYTHON_CMD% -m venv venv || (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/8] Virtual environment already exists. Skipping creation.
)

REM ===============================================
REM 3. Activate the virtual environment
REM ===============================================
echo [3/8] Activating the virtual environment...
call venv\Scripts\activate.bat

REM ===============================================
REM 4. Upgrade pip
REM ===============================================
echo [4/8] Upgrading pip...
python -m pip install --upgrade pip >nul || (
    echo [ERROR] Failed to upgrade pip. Check your internet connection.
    pause
    exit /b 1
)

REM ===============================================
REM 5. Install dependencies from requirements.txt
REM ===============================================
if exist requirements.txt (
    echo [5/8] Installing Python dependencies from requirements.txt...
    pip install -r requirements.txt || (
        echo [ERROR] Failed to install dependencies from requirements.txt.
        echo Please check the file for errors or check your internet connection.
        pause
        exit /b 1
    )
) else (
    echo [ERROR] requirements.txt not found!
    echo Please ensure it is present in the same directory as this installer.
    pause
    exit /b 1
)

REM ===============================================
REM 6. Optional: Install Playwright browsers
REM ===============================================
echo [6/8] Installing Playwright browsers (for web scraping)...
python -m playwright install || (
    echo [WARNING] Failed to install Playwright browsers.
    echo The web search functionality might not work correctly. You can try running 'python -m playwright install' manually later.
    pause
)

REM ===============================================
REM 7. Prompt for API keys and create .env
REM ===============================================
echo [7/8] Setting up API keys...
if exist .env (
    echo .env file already exists. Skipping API key setup.
) else (
    echo.
    echo To enable robust web search, you need a Google Custom Search API key and CSE ID.
    echo - Get your API key here: https://console.developers.google.com/apis/credentials
    echo - Create a Custom Search Engine here: https://cse.google.com/cse/all
    echo - In the CSE setup, add 'www.google.com' as a site to search, and enable 'Search the entire web'.
    echo - Your CSE ID will be in the control panel's 'Basics' tab.
    echo.
    set /p "GKEY=Enter your Google API Key (or press Enter to skip): "
    set /p "GCSE=Enter your Google CSE ID (or press Enter to skip): "
    (
        echo # Environment variables for Shell GPT Research Agent
        echo GOOGLE_API_KEY=!GKEY!
        echo GOOGLE_CSE_ID=!GCSE!
    ) > .env
    echo .env file created. You can edit it manually later if needed.
)

REM ===============================================
REM 8. Run the GUI application
REM ===============================================
echo [8/8] Starting the application...
echo.
python -m sgptAgent.gui_app || (
    echo [ERROR] Failed to start the application.
    echo Ensure all dependencies were installed correctly.
    pause
    exit /b 1
)

echo.
echo ---
echo Installation complete and application started.
echo To run the app again in the future:
echo 1. Open a command prompt in this directory.
echo 2. Activate the virtual environment: venv\Scripts\activate.bat
echo 3. Run the app: python -m sgptAgent.gui_app
echo ---
pause
