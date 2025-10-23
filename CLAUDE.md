# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

git-ai-summary is a command-line tool that analyzes git commit history using AI. It supports 9 different AI providers (OpenAI, Anthropic, Ollama, OpenRouter, Gemini, Cohere, Mistral, LiteLLM, LLM CLI) with flexible configuration and retry logic.

## Core Architecture

### Single-File Design
The entire application is in `git-ai-summary.py` - a self-contained Python script with:
- Provider abstraction via Protocol class (`AIProvider`)
- Provider factory pattern (`make_provider()`)
- Configuration hierarchy (dataclass `Config`)
- Retry logic with exponential backoff (`_make_request_with_retry()`)

### Provider System
Each AI provider is implemented as a class following the `AIProvider` protocol:
- `OpenAIProvider`, `AnthropicProvider`, `OllamaProvider`, etc.
- Each has `generate(system_prompt, user_prompt) -> str` method
- Provider-specific API handling, headers, and response parsing
- Model selection via CLI args or environment config

### Configuration Hierarchy
The `.env` file is searched in this priority order (first found wins):
1. Current directory (`.env`)
2. Git repository root (`.env`)
3. User config (`~/.config/git-ai-summary/.env`)
4. Script installation directory (`.env`)

This allows global settings with project-specific overrides.

## Development Commands

### Environment Setup
```bash
# Using uv (preferred - per user's global CLAUDE.md)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# OR using make
make setup          # Creates venv and installs dependencies
source activate.sh  # Activates the venv
```

### Testing and Validation
```bash
# Type checking
mypy git-ai-summary.py

# Quick test (shows help)
./git-ai-summary.py --help

# Verify setup
./check_setup.sh

# Test with a provider
./git-ai-summary.py --provider anthropic --since HEAD~5
```

### Installation
```bash
# System-wide installation
./install.sh        # Creates ~/bin/git-ai-summary symlink

# Development mode
make setup          # Work locally with venv
```

## Key Components

### Git Integration (`get_commits_since()`)
- Uses `git rev-list` to get commit hashes
- Parses commit metadata (author, timestamp, message)
- Extracts diffs with truncation for large changes
- Auto-detection of sync points via `get_recent_sync_point()`

### Prompt Engineering (`create_ai_prompt()`)
- Focus parameter: "features", "security", "performance"
- Filters diff output to relevant code changes
- Structured format with commit metadata and diffs
- Excludes noise (tests, docs, minor refactoring)

### Retry Logic (`_make_request_with_retry()`)
- Handles HTTP 429 (rate limit) with exponential backoff
- Retries on 5xx server errors
- Timeout and connection error handling
- Configurable via `AI_MAX_RETRIES` and `AI_TIMEOUT_SECONDS`

### Logging
- Structured logging with correlation IDs (UUIDs)
- Request/response timing
- Debug-level config file loading
- Configured via `AI_LOG_LEVEL` environment variable

## Important Implementation Details

### LiteLLM Modes
LiteLLM supports 3 modes (via `LITELLM_MODE`):
- `python`: Uses litellm package directly
- `http`: Connects to LiteLLM proxy server
- `cli`: Invokes litellm CLI command

### API Key Validation
Only validates keys for providers that require them. Ollama (local) and LLM CLI (pre-configured) don't need keys at runtime.

### Clipboard Support
- `--copy`: Copies prompt to clipboard for manual AI input
- `--output-copy`: Copies AI response to clipboard
- Tries `pbcopy` (macOS) first, then `xclip` (Linux)

### Error Handling Philosophy
- Friendly error messages with actionable suggestions
- Provider-specific connection errors (e.g., Ollama not running)
- Configuration errors fail early with clear messages
- Authentication failures distinguished from rate limits

## Configuration

### Required Files
- `.env` or `~/.config/git-ai-summary/.env` with API keys
- `requirements.txt`: python-dotenv>=1.0.0, requests>=2.31.0

### Environment Variables
Provider selection:
- `DEFAULT_AI_PROVIDER`: Which provider to use by default

Per-provider settings (example):
- `ANTHROPIC_API_KEY`: API authentication
- `ANTHROPIC_MODEL`: Model override (e.g., "claude-3-5-sonnet-latest")
- `ANTHROPIC_BASE_URL`: Custom endpoint (rare)

Global settings:
- `AI_TIMEOUT_SECONDS`: Request timeout (default: 30)
- `AI_MAX_RETRIES`: Retry attempts (default: 2)
- `AI_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

## Common Development Scenarios

### Adding a New AI Provider
1. Create provider class implementing `AIProvider` protocol
2. Add to `make_provider()` factory function
3. Add provider type to `ProviderType` Literal
4. Add configuration fields to `Config` dataclass
5. Add to CLI choices in argparse setup
6. Update README.md provider table

### Modifying Prompt Logic
Edit `create_ai_prompt()` - this is where commit analysis strategy lives. Key areas:
- `focus` parameter handling for different analysis types
- Diff filtering logic (what to include/exclude)
- Prompt structure and instructions

### Debugging API Issues
Enable debug logging to see full request/response flow:
```bash
export AI_LOG_LEVEL=DEBUG
./git-ai-summary.py --provider anthropic
```

Check correlation ID in logs to track specific requests through retry logic.

## Testing Strategy

Current state: No automated tests (pytest placeholder in README)

When adding tests, consider:
- Mock HTTP responses for each provider
- Test retry logic with simulated failures
- Config file hierarchy (which .env wins)
- Commit parsing with various git histories
- Error message clarity

## Distribution Model

Designed for both:
1. **Local development**: `source activate.sh` + `./git-ai-summary.py`
2. **System-wide install**: `./install.sh` creates `~/bin/git-ai-summary` wrapper
3. **Wrapper script** (`git-ai-summary-wrapper.sh`): Activates venv and runs main script

The wrapper ensures the venv is always used, even when called from other directories.
