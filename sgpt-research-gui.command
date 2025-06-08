#!/bin/bash
# macOS double-clickable launcher for Shell GPT Research Agent GUI
cd "$(dirname "$0")/sgptAgent"
PYTHONPATH="$(dirname "$PWD")" ../venv/bin/python gui_app.py "$@"
