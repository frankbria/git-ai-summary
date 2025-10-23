.PHONY: help setup install check clean test activate

help:
	@echo "Git AI Summary - Available Commands"
	@echo ""
	@echo "  make setup     - Create virtual environment and install dependencies"
	@echo "  make check     - Verify setup is correct"
	@echo "  make clean     - Remove virtual environment"
	@echo "  make install   - Install additional optional packages"
	@echo ""
	@echo "Usage after setup:"
	@echo "  source activate.sh              - Activate virtual environment"
	@echo "  ./git-ai-summary.py --help      - Show script help"
	@echo "  ./git-ai-summary.py --provider anthropic  - Run with a provider"

setup:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. cp .env.example .env"
	@echo "2. Edit .env with your API key"
	@echo "3. source activate.sh"
	@echo "4. ./git-ai-summary.py --provider <your-provider>"

install:
	@echo "Installing optional packages..."
	./venv/bin/pip install litellm llm
	@echo "✓ Optional packages installed"

check:
	@./check_setup.sh

clean:
	@echo "Removing virtual environment..."
	rm -rf venv
	@echo "✓ Cleaned"

test:
	@echo "Running script test..."
	./venv/bin/python git-ai-summary.py --help
	@echo ""
	@echo "✓ Script works!"
