@echo off
REM Shell GPT Research Agent - Windows Installer

REM 1. Check for Python installation
where python >nul 2>nul || where python3 >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.8 or newer and re-run this installer.
    pause
    exit /b 1
)

REM 2. Create a virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv || python3 -m venv venv
)

REM 3. Activate the virtual environment
call venv\Scripts\activate.bat

REM 4. Upgrade pip
python -m pip install --upgrade pip

REM 5. Install dependencies
if exist requirements.txt (
    echo Installing Python dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found! Please ensure it is present in the project directory.
    pause
    exit /b 1
)

REM 6. Optional: Install Playwright browsers (for web search scraping)
python -m playwright install

REM 7. Prompt for API keys and create .env if needed
if exist .env (
    echo .env file already exists. Skipping API key setup.
) else (
    echo.
    echo To enable robust web search, you need a Google Custom Search API key and CSE ID.
    echo - Get your API key here: https://console.developers.google.com/apis/credentials
    echo - Create a Custom Search Engine here: https://cse.google.com/cse/all
    echo - Add 'www.google.com' as a site to search (for full web search, enable 'Search the entire web').
    echo - Find your CSE ID in the control panel.
    set /p GKEY=Enter your Google API Key: 
    set /p GCSE=Enter your Google CSE ID: 
    (echo GOOGLE_API_KEY=%GKEY%) > .env
    (echo GOOGLE_CSE_ID=%GCSE%) >> .env
    echo .env file created with your credentials.
)

REM 8. Run the GUI application
python -m sgptAgent.gui_app

echo Installation complete. To run the app in the future:
echo 1. Activate the virtual environment: call venv\Scripts\activate.bat
echo 2. Run the app: python -m sgptAgent.gui_app
pause
