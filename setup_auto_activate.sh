#!/bin/bash
# Setup script to configure automatic venv activation
# This script offers multiple methods for auto-activation

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_RC="$HOME/.zshrc"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MS Copilot Automation - Auto-Activation Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose an auto-activation method:"
echo ""
echo "1) direnv (recommended - works globally)"
echo "   - Install: brew install direnv"
echo "   - Automatically activates when entering directory"
echo ""
echo "2) Shell function (add to ~/.zshrc)"
echo "   - Activates when you 'cd' to this directory"
echo "   - No additional tools needed"
echo ""
echo "3) Manual (no auto-activation)"
echo "   - Run 'source activate_venv.sh' when needed"
echo ""
read -p "Select option (1-3): " choice

case $choice in
  1)
    echo ""
    echo "Setting up direnv..."
    
    # Check if direnv is installed
    if ! command -v direnv &> /dev/null; then
      echo "⚠️  direnv not found. Installing with Homebrew..."
      if command -v brew &> /dev/null; then
        brew install direnv
      else
        echo "❌ Homebrew not found. Install direnv manually:"
        echo "   brew install direnv"
        exit 1
      fi
    fi
    
    # Add direnv hook to shell if not present
    if ! grep -q "direnv hook zsh" "$SHELL_RC" 2>/dev/null; then
      echo "" >> "$SHELL_RC"
      echo "# direnv hook for auto-activation" >> "$SHELL_RC"
      echo 'eval "$(direnv hook zsh)"' >> "$SHELL_RC"
      echo "✓ Added direnv hook to $SHELL_RC"
    else
      echo "✓ direnv hook already in $SHELL_RC"
    fi
    
    # Allow direnv for this directory
    cd "$PROJECT_DIR"
    direnv allow
    
    echo ""
    echo "✓ direnv setup complete!"
    echo "  Restart your terminal or run: source ~/.zshrc"
    echo "  Then cd into this directory to auto-activate"
    ;;
    
  2)
    echo ""
    echo "Setting up shell function..."
    
    FUNC_CODE="
# Auto-activate venv for ms_copilot_automation project
function cd() {
  builtin cd \"\$@\"
  if [[ \"\$PWD\" == \"$PROJECT_DIR\"* ]] && [[ -f \"$PROJECT_DIR/venv/bin/activate\" ]]; then
    if [[ \"\$VIRTUAL_ENV\" != \"$PROJECT_DIR/venv\" ]]; then
      source \"$PROJECT_DIR/venv/bin/activate\"
      echo \"✓ Virtual environment activated\"
    fi
  fi
}
"
    
    if ! grep -q "ms_copilot_automation project" "$SHELL_RC" 2>/dev/null; then
      echo "$FUNC_CODE" >> "$SHELL_RC"
      echo "✓ Added auto-activation function to $SHELL_RC"
    else
      echo "✓ Auto-activation function already in $SHELL_RC"
    fi
    
    echo ""
    echo "✓ Shell function setup complete!"
    echo "  Restart your terminal or run: source ~/.zshrc"
    echo "  Then cd into this directory to auto-activate"
    ;;
    
  3)
    echo ""
    echo "Manual mode selected."
    echo "To activate the virtual environment, run:"
    echo "  source activate_venv.sh"
    echo ""
    echo "Or directly:"
    echo "  source venv/bin/activate"
    ;;
    
  *)
    echo "Invalid option. Exiting."
    exit 1
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
