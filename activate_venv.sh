#!/bin/bash
# Simple activation script
# Usage: source activate_venv.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
echo "✓ Virtual environment activated for ms_copilot_automation"
echo "  Python: $(which python)"
echo "  ms-copilot CLI available: $(which ms-copilot)"


