#!/bin/bash
# ============================================================================
#  Installation script for Unified CLI Profile Manager
# ============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${AI_MAN_INSTALL_BIN_DIR:-$HOME/.local/bin}"
LINK_AI="$BIN_DIR/ai-man"
LINK_LONG="$BIN_DIR/profile-man"
LINK_SHORT="$BIN_DIR/pman"

echo "Installing Unified CLI Profile Manager..."

# Make python script executable
chmod +x "$PROJECT_DIR/profile_manager.py"

# Create local bin if it doesn't exist
mkdir -p "$BIN_DIR"

install_link() {
    local link_path="$1"
    if [ -e "$link_path" ] || [ -L "$link_path" ]; then
        rm "$link_path"
    fi
    ln -s "$PROJECT_DIR/profile_manager.py" "$link_path"
}

install_link "$LINK_AI"
install_link "$LINK_LONG"
install_link "$LINK_SHORT"

echo ""
echo "Installation complete!"
echo "You can now launch the manager using the command: ai-man (or profile-man / pman)"
echo "Note: Make sure $BIN_DIR is in your shell PATH."
echo "Verify with: $PROJECT_DIR/scripts/verify_install.sh"
