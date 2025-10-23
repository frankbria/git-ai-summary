#!/bin/bash
# Source this file to activate the virtual environment
# Usage: source activate.sh

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo "Python: $(which python)"
    echo "Version: $(python --version)"
    echo ""
    echo "To run the script:"
    echo "  ./git-ai-summary.py --provider <provider>"
    echo ""
    echo "To deactivate:"
    echo "  deactivate"
else
    echo "Error: Virtual environment not found at ./venv"
    echo "Run: python3 -m venv venv"
fi
