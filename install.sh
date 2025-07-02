#!/usr/bin/env bash
set -e

# Colors for output
green="\033[0;32m"
red="\033[0;31m"
yellow="\033[1;33m"
reset="\033[0m"

# Helper for graceful error
fail() {
    echo -e "${red}ERROR:${reset} $1"
    exit 1
}

# Welcome
cat <<EOF
${green}
Shell GPT Research Agent - Interactive Installer
${reset}
This script will help you set up the research agent, including dependencies, API keys, and Ollama LLM backend.
EOF

# Step 1: Python version
if ! command -v python3 &>/dev/null; then
    fail "Python 3 is required. Please install Python 3.8 or newer."
fi
PYMAJ=$(python3 -c 'import sys; print(sys.version_info[0])')
PYMIN=$(python3 -c 'import sys; print(sys.version_info[1])')
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 8 ]; }; then
    fail "Python version $PYMAJ.$PYMIN found. Python 3.8+ is required."
fi
PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo -e "${green}✔ Python 3 detected (${PYV})${reset}"

# Step 2: Virtual environment
if [ ! -d "venv" ]; then
    echo -e "${yellow}Creating Python virtual environment...${reset}"
    python3 -m venv venv || fail "Failed to create virtualenv."
else
    echo -e "${green}✔ Virtual environment already exists${reset}"
fi
source venv/bin/activate

echo -e "${green}✔ Virtual environment activated${reset}"

# Ensure pip is present in the venv
if [ ! -x "venv/bin/pip" ]; then
    echo -e "${red}pip is missing from the virtual environment.${reset}"
    echo -e "If you are on Debian/Ubuntu, this is due to system Python restrictions."
    echo -e "To fix:"
    echo -e "  1. Run: sudo apt install python3-pip"
    echo -e "  2. Delete the venv directory: rm -rf venv"
    echo -e "  3. Re-run this installer."
    exit 1
fi

# Step 3: Pip dependencies
echo -e "${yellow}Installing Python requirements...${reset}"
echo -e "${yellow}The following packages will be installed for enhanced research capabilities:${reset}"
echo -e "  - spacy + nltk (Advanced NLP for entity recognition and query enhancement)"
echo -e "  - scikit-learn (Relevance scoring and text similarity)"
echo -e "  - fuzzywuzzy (Fuzzy text matching)"
echo -e "  - sentence-transformers (Semantic similarity)"
echo -e "  - markdown2 (HTML export)"
echo -e "  - reportlab (PDF export)"
echo -e "  - python-docx (Word DOCX export)"
./venv/bin/pip install --upgrade pip

PIP_FLAGS=""
if [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -ge 12 ]; then
    echo -e "${yellow}Detected Python 3.12+. Using --break-system-packages for pip due to PEP 668 (Debian/Ubuntu restriction).${reset}"
    PIP_FLAGS="--break-system-packages"
fi
if ! ./venv/bin/pip install -r requirements.txt $PIP_FLAGS; then
    echo -e "${red}Failed to install Python dependencies. If you see an error about 'externally-managed-environment', try deleting the venv directory and rerunning the script, or manually run: ./venv/bin/pip install --break-system-packages -r requirements.txt${reset}"
    exit 1
fi

echo -e "${green}✔ Python dependencies installed successfully${reset}"

# Step 3.5: Download NLP models and data
echo -e "${yellow}Setting up NLP models and data...${reset}"

# Download spaCy English model
echo -e "${yellow}Downloading spaCy English model (en_core_web_sm)...${reset}"
if ! ./venv/bin/python -m spacy download en_core_web_sm; then
    echo -e "${red}Failed to download spaCy English model. Trying alternative method...${reset}"
    if ! ./venv/bin/pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl $PIP_FLAGS; then
        echo -e "${red}Failed to install spaCy model. The application will fall back to basic entity extraction.${reset}"
    else
        echo -e "${green}✔ spaCy English model installed via direct download${reset}"
    fi
else
    echo -e "${green}✔ spaCy English model downloaded successfully${reset}"
fi

# Download NLTK data
echo -e "${yellow}Downloading NLTK data (wordnet, punkt, stopwords)...${reset}"
./venv/bin/python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True) 
    nltk.download('stopwords', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    print('✔ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠ NLTK download warning: {e}')
    print('The application will work with reduced query enhancement capabilities')
"

echo -e "${green}✔ NLP setup completed. Enhanced query construction and entity recognition are now available.${reset}"

# Step 4: Playwright browser dependencies
echo -e "${yellow}Installing Playwright browsers (for robust extraction)...${reset}"
./venv/bin/python -m playwright install || fail "Failed to install Playwright browsers."

# Step 5: Ollama install and model selection
if ! command -v ollama &>/dev/null; then
    echo -e "${yellow}Ollama not found. Installing Ollama...${reset}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh || fail "Failed to install Ollama. See https://ollama.com/download for manual instructions."
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            brew install ollama || fail "Failed to install Ollama via Homebrew. See https://ollama.com/download for manual instructions."
        else
            echo -e "${red}Homebrew not found. Please install Ollama manually from https://ollama.com/download${reset}"
        fi
    else
        echo -e "${red}Automatic Ollama install is only supported on Linux and macOS (with Homebrew). Please install manually from https://ollama.com/download${reset}"
    fi
else
    echo -e "${green}✔ Ollama is already installed${reset}"
fi

# Step 6: List models and let user choose
MODEL_API="https://ollama.com/library/api"
MODEL_LIST=""
MODEL_NAMES=()
MODEL_IDS=()

# Try to get model list from API
if command -v curl &>/dev/null && curl -fsSL "$MODEL_API" | grep -q '"name"'; then
    MODEL_LIST=$(curl -fsSL "$MODEL_API" | grep '"name"' | sed 's/.*"name": "\([^"]*\)".*/\1/')
    IFS=$'\n' read -rd '' -a MODEL_NAMES <<<"$MODEL_LIST"
else
    # Fallback static list
    MODEL_NAMES=("llama3" "llama2" "phi3" "mistral" "gemma" "codellama" "neural-chat" "dolphin-mixtral" "llava")
fi

echo -e "\n${yellow}Available Ollama models:${reset}"
select MODEL in "${MODEL_NAMES[@]}"; do
    if [[ -n "$MODEL" ]]; then
        echo -e "${green}You selected: $MODEL${reset}"
        break
    else
        echo -e "${red}Invalid selection. Please choose a model by number.${reset}"
    fi
done

if ! ollama list | grep -q "$MODEL"; then
    echo -e "${yellow}Pulling selected model '$MODEL' for Ollama...${reset}"
    ollama pull "$MODEL" || echo -e "${red}Failed to pull model. You may need to do this manually: 'ollama pull $MODEL'${reset}"
else
    echo -e "${green}✔ Ollama model '$MODEL' is present${reset}"
fi

# Step 7: Google CSE API setup
cat <<APITIP

${yellow}To enable robust web search, you need a Google Custom Search API key and CSE ID.${reset}
- Get your API key here: https://console.developers.google.com/apis/credentials
- Create a Custom Search Engine here: https://cse.google.com/cse/all
- Add 'www.google.com' as a site to search (for full web search, enable 'Search the entire web').
- Find your CSE ID in the control panel.

${yellow}When you have both values, enter them below.${reset}
APITIP

envfile=".env"
if [ -f "$envfile" ]; then
    echo -e "${green}✔ .env file already exists. Skipping creation.${reset}"
else
    read -p "Enter your Google API Key: " GKEY
    read -p "Enter your Google CSE ID: " GCSE
    echo "GOOGLE_API_KEY=$GKEY" > "$envfile"
    echo "GOOGLE_CSE_ID=$GCSE" >> "$envfile"
    echo -e "${green}✔ .env file created with your credentials${reset}"
fi

# Step 8: Create CLI alias for sgpt-research
BIN_ALIAS="$HOME/.local/bin/sgpt-research"
SCRIPT_PATH="$PWD/launch_sgpt_research.sh"
mkdir -p "$HOME/.local/bin"
ln -sf "$SCRIPT_PATH" "$BIN_ALIAS"
chmod +x "$BIN_ALIAS"
echo -e "${green}✔ sgpt-research CLI alias created at ~/.local/bin/sgpt-research${reset}"
echo -e "\nYou can now launch the research agent from anywhere with:"
echo -e "  ${yellow}sgpt-research${reset}"

# --- Linux Desktop Launcher Install ---
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${yellow}Installing desktop launcher for Linux...${reset}"
    LAUNCHER_SRC="$PWD/sgpt-research-gui.desktop"
    LAUNCHER_DEST="$HOME/.local/share/applications/sgpt-research-gui.desktop"
    ICON_SRC="$PWD/sgptAgent/Assets/sgptRAicon.png"
    ICON_DEST="$HOME/.local/share/icons/sgptRAicon.png"
    mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons"
    cp "$LAUNCHER_SRC" "$LAUNCHER_DEST"
    if command -v convert &>/dev/null; then
        convert "$ICON_SRC" -resize 128x128 "$ICON_DEST"
    else
        cp "$ICON_SRC" "$ICON_DEST"
    fi
    # Update icon path in .desktop file
    sed -i "s|^Icon=.*|Icon=$ICON_DEST|" "$LAUNCHER_DEST"
    update-desktop-database "$HOME/.local/share/applications/" || true
    echo -e "${green}✔ GUI launcher installed! You can now find 'Shell GPT Research Agent GUI' in your app menu or search.${reset}"
fi

echo -e "${green}✔ Installation complete!${reset}"

# Final verification step
echo -e "${yellow}Running setup verification...${reset}"
if ./venv/bin/python verify_setup.py; then
    echo -e "${green}✔ All systems verified and ready!${reset}"
else
    echo -e "${yellow}⚠ Some verification tests failed, but the application should still work.${reset}"
fi

echo -e "${green}
🎉 Shell GPT Research Agent is ready to use!

Enhanced AI capabilities now available:
  • Advanced entity recognition with spaCy
  • Query expansion with NLTK WordNet  
  • Relevance scoring with TF-IDF
  • Domain-specific query enhancement
  • Progressive fallback strategies
  • Fuzzy text matching

Creating desktop launcher...${reset}"

# Create desktop file with correct paths
./create_desktop_file.sh

echo -e "${green}
To run the application:
  CLI: ./launch_sgpt_research.sh
  GUI: ./sgpt-research-gui or double-click sgpt-research-gui.desktop
  
Or directly:
  source venv/bin/activate && python sgptAgent/gui_app.py

To verify setup anytime:
  source venv/bin/activate && python verify_setup.py
${reset}"
