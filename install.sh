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

# Step 4: Playwright browser dependencies
echo -e "${yellow}Installing Playwright browsers (for robust extraction)...${reset}"
python -m playwright install || fail "Failed to install Playwright browsers."

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
echo -e "\nTo launch the research agent, run:"
echo -e "  ${yellow}./launch_sgpt_research.sh${reset}"
echo -e "\nTo activate the venv manually:"
echo -e "  ${yellow}source venv/bin/activate${reset}"
echo -e "\nHappy researching!"
