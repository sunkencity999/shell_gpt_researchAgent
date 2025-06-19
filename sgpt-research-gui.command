#!/bin/bash
# macOS double-clickable launcher for Shell GPT Research Agent GUI

# Resolve the directory of this script, following symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# Check if venv exists
if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
    echo "[ERROR] Python venv not found! Please run install.sh first."
    read -p "Press any key to continue..."
    exit 1
fi

# Set up environment
export PYTHONPATH="$SCRIPT_DIR"
cd "$SCRIPT_DIR"

# Load .env variables if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Launch GUI
"$SCRIPT_DIR/venv/bin/python" sgptAgent/gui_app.py "$@"

# Keep terminal open on macOS for any error messages
if [ $? -ne 0 ]; then
    echo "Press any key to close..."
    read -n 1
fi
