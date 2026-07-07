#!/bin/bash
# ============================================================================
#  Installation script for Unified CLI Profile Manager
# ============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
LINK_AI="$BIN_DIR/ai-man"
LINK_LONG="$BIN_DIR/profile-man"
LINK_SHORT="$BIN_DIR/pman"

echo "Installing Unified CLI Profile Manager..."

# Make python script executable
chmod +x "$PROJECT_DIR/profile_manager.py"

# Create local bin if it doesn't exist
mkdir -p "$BIN_DIR"

# Create symlink: ai-man
if [ -L "$LINK_AI" ] || [ -f "$LINK_AI" ]; then
    rm "$LINK_AI"
fi
ln -s "$PROJECT_DIR/profile_manager.py" "$LINK_AI"

# Create symlink: profile-man
if [ -L "$LINK_LONG" ] || [ -f "$LINK_LONG" ]; then
    rm "$LINK_LONG"
fi
ln -s "$PROJECT_DIR/profile_manager.py" "$LINK_LONG"

# Create symlink: pman
if [ -L "$LINK_SHORT" ] || [ -f "$LINK_SHORT" ]; then
    rm "$LINK_SHORT"
fi
ln -s "$PROJECT_DIR/profile_manager.py" "$LINK_SHORT"

echo ""
echo "Installation complete!"
echo "You can now launch the manager using the command: ai-man (or profile-man / pman)"
echo "Note: Make sure $BIN_DIR is in your shell PATH."
