#!/bin/bash
# Wrapper script for git-ai-summary
# This allows the tool to work from any directory with proper venv activation

# Resolve the real path of this script (follow symlinks)
REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$REAL_SCRIPT")"

# Activate the virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the Python script with all arguments
exec python "$SCRIPT_DIR/git-ai-summary.py" "$@"
