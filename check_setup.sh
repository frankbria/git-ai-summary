#!/bin/bash
# Verify that the git-ai-summary environment is properly set up

echo "=== Git AI Summary - Setup Verification ==="
echo ""

# Check if we're in the right directory
if [ ! -f "git-ai-summary.py" ]; then
    echo "❌ Error: Run this script from the git-ai-summary directory"
    exit 1
fi

echo "✓ In correct directory"

# Check for virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
    
    # Check if venv has Python
    if [ -f "venv/bin/python" ]; then
        echo "✓ Python installed in venv: $(venv/bin/python --version)"
    else
        echo "❌ Python not found in venv"
        exit 1
    fi
    
    # Check installed packages
    echo ""
    echo "Installed packages:"
    venv/bin/pip list | grep -E "(python-dotenv|requests)"
    
    if venv/bin/pip list | grep -q "python-dotenv" && venv/bin/pip list | grep -q "requests"; then
        echo "✓ Required packages installed"
    else
        echo "❌ Missing required packages"
        echo "Run: venv/bin/pip install -r requirements.txt"
        exit 1
    fi
else
    echo "❌ Virtual environment not found"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Check for configuration files
echo ""
if [ -f ".env.example" ]; then
    echo "✓ .env.example exists"
else
    echo "⚠ .env.example not found"
fi

if [ -f ".env" ]; then
    echo "✓ .env file exists (configuration present)"
else
    echo "⚠ .env file not found (you'll need to create it)"
    echo "  Run: cp .env.example .env"
fi

# Check script permissions
echo ""
if [ -x "git-ai-summary.py" ]; then
    echo "✓ git-ai-summary.py is executable"
else
    echo "⚠ git-ai-summary.py not executable"
    echo "  Run: chmod +x git-ai-summary.py"
fi

# Test script can run
echo ""
echo "Testing script..."
if venv/bin/python git-ai-summary.py --help > /dev/null 2>&1; then
    echo "✓ Script runs successfully"
else
    echo "❌ Script failed to run"
    venv/bin/python git-ai-summary.py --help
    exit 1
fi

# Summary
echo ""
echo "=== Setup Status ==="
if [ -f ".env" ]; then
    echo "✓ Ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env with your API key"
    echo "2. Activate venv: source activate.sh"
    echo "3. Run: ./git-ai-summary.py --provider <your-provider>"
else
    echo "⚠ Almost ready!"
    echo ""
    echo "Next steps:"
    echo "1. Create .env: cp .env.example .env"
    echo "2. Edit .env with your API key"
    echo "3. Activate venv: source activate.sh"
    echo "4. Run: ./git-ai-summary.py --provider <your-provider>"
fi

echo ""
echo "For help, see QUICKSTART.md or README.md"
