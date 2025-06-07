#!/bin/bash
# Shell GPT Research Agent Launcher
# Robustly supports being run via symlink from any directory.

# Resolve the directory of this script, following symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$SCRIPT_DIR"

# Use only the venv's python. Fail if venv is missing.
if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
    echo "[ERROR] Python venv not found in $SCRIPT_DIR! Please run install.sh first."
    exit 1
fi
PYTHON="$SCRIPT_DIR/venv/bin/python"

export PYTHONPATH="$SCRIPT_DIR"

# Load .env variables if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

echo "[DEBUG] Using python: $PYTHON"
$PYTHON -m sgptAgent.__main__
