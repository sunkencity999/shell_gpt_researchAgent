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
REM 5. Install Python requirements
REM ===============================================
echo [5/8] Installing Python requirements from requirements.txt...
echo Enhanced research capabilities will be installed:
echo   - spacy + nltk (Advanced NLP for entity recognition and query enhancement)
echo   - scikit-learn (Relevance scoring and text similarity)
echo   - fuzzywuzzy (Fuzzy text matching)
echo   - sentence-transformers (Semantic similarity)
echo   - Export features (markdown2, reportlab, python-docx, PyPDF2)
venv\Scripts\pip install -r requirements.txt || (
    echo [ERROR] Failed to install Python requirements.
    pause
    exit /b 1
)
echo [5/8] Requirements installed.

REM ===============================================
REM 5.5. Setup NLP models and data
REM ===============================================
echo [5.5/8] Setting up NLP models and data...

REM Download spaCy English model
echo Downloading spaCy English model (en_core_web_sm)...
venv\Scripts\python -m spacy download en_core_web_sm || (
    echo [WARNING] Failed to download spaCy English model via spacy command.
    echo Trying alternative method...
    venv\Scripts\pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || (
        echo [WARNING] Failed to install spaCy model. The application will fall back to basic entity extraction.
    )
)

REM Download NLTK data
echo Downloading NLTK data (wordnet, punkt, stopwords)...
venv\Scripts\python -c "import nltk; import ssl; ssl._create_default_https_context = ssl._create_unverified_context; nltk.download('wordnet', quiet=True); nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('omw-1.4', quiet=True); print('NLTK data downloaded successfully')" || (
    echo [WARNING] NLTK data download failed. The application will work with reduced query enhancement capabilities.
)

echo [5.5/8] NLP setup completed. Enhanced query construction and entity recognition are now available.

echo [6/8] Pulling Ollama embedding model 'nomic-embed-text'...
ollama pull nomic-embed-text || (
    echo [WARNING] Failed to pull embedding model from Ollama.
    echo Please ensure Ollama is running and try again manually: ollama pull nomic-embed-text
    pause
)

echo [6.5/8] Pulling Ollama multimodal model 'llava'...
ollama pull llava || (
    echo [WARNING] Failed to pull multimodal model from Ollama.
    echo Please ensure Ollama is running and try again manually: ollama pull llava
    pause
)

REM ===============================================
REM 7. Re-run requirements.txt to ensure sentence-transformers is installed
REM ===============================================
echo [7/8] Re-installing Python requirements to ensure embedding dependencies...
venv\Scripts\pip install -r requirements.txt || (
    echo [ERROR] Failed to re-install Python requirements.
    pause
    exit /b 1
)
echo [7/8] Embedding dependencies ensured.

REM ===============================================
REM 8. Install dependencies from requirements.txt
REM ===============================================
if exist requirements.txt (
    echo [8/8] Installing Python dependencies from requirements.txt...
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
call venv\Scripts\python -m playwright install || (
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

echo [8/8] Installation complete!

REM Final verification step
echo Running setup verification...
venv\Scripts\python verify_setup.py
if %errorlevel% equ 0 (
    echo All systems verified and ready!
) else (
    echo Some verification tests failed, but the application should still work.
)

echo.
echo 🎉 Shell GPT Research Agent is ready to use!
echo.
echo Enhanced AI capabilities now available:
echo   • Advanced entity recognition with spaCy
echo   • Query expansion with NLTK WordNet
echo   • Relevance scoring with TF-IDF
echo   • Domain-specific query enhancement
echo   • Progressive fallback strategies
echo   • Fuzzy text matching
echo.
echo.
echo To run the application:
echo   GUI: venv\Scripts\python sgptAgent\gui_app.py
echo   Web UI: launch_web.bat
echo.
echo To verify setup anytime:
echo   venv\Scripts\python verify_setup.py
echo.