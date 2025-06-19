#!/bin/bash
# Script to create a desktop file with correct paths for the current installation

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the desktop file
cat > "$SCRIPT_DIR/sgpt-research-gui.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Shell GPT Research Agent GUI
Comment=Local research agent with LLM synthesis and web search
Exec=$SCRIPT_DIR/sgpt-research-gui
Icon=$SCRIPT_DIR/sgptAgent/Assets/sgptRAicon.png
Path=$SCRIPT_DIR
Terminal=false
Categories=Science;Education;
StartupNotify=true
Keywords=AI;Research;LLM;Agent;Analysis;
EOF

# Make the desktop file executable
chmod +x "$SCRIPT_DIR/sgpt-research-gui.desktop"

echo "Desktop file created at: $SCRIPT_DIR/sgpt-research-gui.desktop"
echo "You can now:"
echo "1. Double-click the desktop file to launch the GUI"
echo "2. Copy it to ~/.local/share/applications/ to add it to your application menu"
echo "3. Copy it to your desktop for easy access"
