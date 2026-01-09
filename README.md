# Git AI Summary

[![Follow on X](https://img.shields.io/twitter/follow/FrankBria18044?style=social)](https://x.com/FrankBria18044)

Analyze recent git changes using AI providers of your choice. Supports multiple AI providers including OpenAI, Anthropic Claude, local Ollama, OpenRouter, Google Gemini, Cohere, Mistral AI, LiteLLM, and LLM CLI.

## Features

- **Multi-Provider Support**: Choose from 9 different AI providers
- **Flexible Configuration**: Environment-based configuration with CLI overrides
- **Automatic Commit Detection**: Smart detection of recent sync points
- **Focus Options**: Analyze commits with different focuses (features, security, performance)
- **Clipboard Integration**: Copy prompts or results directly to clipboard
- **Retry Logic**: Built-in retry mechanism with exponential backoff
- **Structured Logging**: Correlation IDs for request tracking
- **Robust Installation** (v1.1): Pre-flight checks, shell auto-detection, atomic rollback
- **Health Check** (v1.1): Verify configuration and connectivity
- **Dry-Run Mode** (v1.1): Preview prompts and estimate costs before API calls
- **Config Validation** (v1.1): Validate configuration syntax without network calls
- **Version Info** (v1.1): Display version information

## Documentation

- **[README.md](README.md)** - This file (user guide and quick start)
- **[INSTALL.md](INSTALL.md)** - Detailed installation guide with troubleshooting
- **[REQUIREMENTS.md](REQUIREMENTS.md)** - Functional and non-functional requirements
- **[PRD.md](PRD.md)** - Product roadmap and feature planning (v1.1+)
- **[TESTING.md](TESTING.md)** - Testing strategy and implementation guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Design decisions and architecture
- **[WORKFLOW.md](WORKFLOW.md)** - Implementation workflow for v1.1
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code

## Installation

### Option 1: System-wide Installation (Recommended)

For system-wide access from any directory:

```bash
./install.sh
```

**New in v1.1**: Enhanced installation with:
- ✅ Pre-flight checks (Python 3.8+, Git, disk space, permissions)
- ✅ Automatic shell detection (bash, zsh, fish)
- ✅ Atomic installation with rollback on failure
- ✅ Post-install validation
- ✅ Detailed installation logging

This creates `~/bin/git-ai-summary` and sets up `~/.config/git-ai-summary/.env` for global configuration.

See [INSTALL.md](INSTALL.md) for detailed installation instructions, configuration scenarios, and troubleshooting.

### Option 2: Local Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source activate.sh  # or: source venv/bin/activate

# Dependencies are already installed in venv
# If needed: pip install -r requirements.txt
```

### Option 2: System-wide

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure your preferred provider:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and preferences:

```env
# Set your default provider
DEFAULT_AI_PROVIDER=anthropic

# Add your API key for the provider(s) you want to use
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
# ... etc
```

### Provider Requirements

| Provider | Required Variable | Optional Variables |
|----------|------------------|-------------------|
| **openai** | `OPENAI_API_KEY` | `OPENAI_MODEL`, `OPENAI_BASE_URL` |
| **anthropic** | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL` |
| **openrouter** | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL` |
| **gemini** | `GOOGLE_API_KEY` | `GEMINI_MODEL`, `GEMINI_BASE_URL` |
| **cohere** | `COHERE_API_KEY` | `COHERE_MODEL`, `COHERE_BASE_URL` |
| **mistral** | `MISTRAL_API_KEY` | `MISTRAL_MODEL`, `MISTRAL_BASE_URL` |
| **ollama** | None (local) | `OLLAMA_MODEL`, `OLLAMA_BASE_URL` |
| **litellm** | Varies by mode | `LITELLM_MODE`, `LITELLM_MODEL`, `LITELLM_BASE_URL` |
| **llm** | None (configured in tool) | `LLM_MODEL`, `LLM_EXTRA_ARGS` |

## Usage

> 💡 **New to clipboard options?** See [CLIPBOARD_GUIDE.md](CLIPBOARD_GUIDE.md) for detailed workflows and examples.

### Diagnostic Commands (v1.1)

Before running analysis, validate your configuration:

```bash
# Check version
./git-ai-summary.py --version

# Validate configuration file
./git-ai-summary.py --validate-config --provider anthropic

# Test connectivity and verify setup
./git-ai-summary.py --health-check --provider anthropic

# Preview prompt and estimate cost (no API call made)
./git-ai-summary.py --dry-run --provider anthropic
```

### Basic Usage

Analyze commits using your default provider:

```bash
./git-ai-summary.py --provider anthropic
```

### Specify a Model

Override the default model:

```bash
./git-ai-summary.py --provider openai --model gpt-4o
```

### Custom Commit Range

```bash
./git-ai-summary.py --provider anthropic --since HEAD~20 --until HEAD
```

### Focus on Specific Aspects

```bash
./git-ai-summary.py --provider openai --focus security
./git-ai-summary.py --provider anthropic --focus performance
```

### Save Analysis to File

```bash
./git-ai-summary.py --provider openai --output analysis.md
```

### Copy Prompt to Clipboard (for manual AI input)

```bash
./git-ai-summary.py --copy
# Then paste into ChatGPT, Claude web interface, etc.
```

### Copy Analysis to Clipboard

```bash
./git-ai-summary.py --provider anthropic --output-copy
```

### Combined Workflows

```bash
# Save analysis to file and copy to clipboard
./git-ai-summary.py --provider openai --output report.md --output-copy

# Copy prompt for manual AI, then run automated analysis too
./git-ai-summary.py --copy
./git-ai-summary.py --provider anthropic --output analysis.md

# Full workflow: analyze, save, and copy
./git-ai-summary.py --provider anthropic --since HEAD~20 --focus security --output security-report.md --output-copy
```

## Provider-Specific Examples

### OpenAI (GPT-4)

```bash
./git-ai-summary.py --provider openai --model gpt-4o-mini
```

### Anthropic (Claude)

```bash
./git-ai-summary.py --provider anthropic --model claude-3-5-sonnet-latest
```

### Local Ollama

First, make sure Ollama is running and you have a model installed:

```bash
ollama run llama3.1:8b
```

Then use the provider:

```bash
./git-ai-summary.py --provider ollama --model llama3.1:8b
```

### OpenRouter

```bash
./git-ai-summary.py --provider openrouter --model anthropic/claude-3.5-sonnet
```

### Google Gemini

```bash
./git-ai-summary.py --provider gemini --model gemini-1.5-flash
```

### Cohere

```bash
./git-ai-summary.py --provider cohere --model command-r-plus
```

### Mistral AI

```bash
./git-ai-summary.py --provider mistral --model mistral-large-latest
```

### LiteLLM

LiteLLM supports three modes:

**Python mode** (uses LiteLLM package):
```bash
# Set in .env: LITELLM_MODE=python
./git-ai-summary.py --provider litellm --model gpt-4o-mini
```

**HTTP mode** (uses LiteLLM proxy server):
```bash
# Set in .env: LITELLM_MODE=http, LITELLM_BASE_URL=http://localhost:4000
./git-ai-summary.py --provider litellm
```

**CLI mode** (uses LiteLLM CLI):
```bash
# Set in .env: LITELLM_MODE=cli
./git-ai-summary.py --provider litellm --model gpt-4o-mini
```

### LLM CLI (Simon Willison)

First, make sure you have the `llm` CLI installed and configured:

```bash
pip install llm
llm keys set openai  # or your preferred provider
```

Then use the provider:

```bash
./git-ai-summary.py --provider llm --model gpt-4o-mini
```

## Troubleshooting

### Authentication Errors

If you get authentication errors:

1. Check that your API key is correctly set in `.env`
2. Verify the key has not expired
3. Ensure you have sufficient credits/quota

### Ollama Connection Failed

If you can't connect to Ollama:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if needed
ollama serve

# Pull the model if not installed
ollama pull llama3.1:8b
```

### Rate Limiting

The tool automatically retries with exponential backoff on rate limit errors (429). You can adjust retry settings in `.env`:

```env
AI_MAX_RETRIES=3
AI_TIMEOUT_SECONDS=60
```

### LLM CLI Not Found

For the `llm` provider:

```bash
pip install llm
llm --version
```

For LiteLLM CLI mode:

```bash
pip install litellm
litellm --version
```

## Advanced Configuration

### Logging

Adjust log verbosity:

```env
AI_LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
```

### Timeouts and Retries

```env
AI_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=2
```

### Provider-Specific Settings

#### OpenRouter

```env
OPENROUTER_SITE_URL=https://github.com/your/repo
OPENROUTER_APP_NAME=git-ai-summary
```

#### LiteLLM

```env
LITELLM_MODE=python  # or http, cli
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=your_proxy_key
```

#### LLM CLI

```env
LLM_EXTRA_ARGS=--no-stream --temperature 0.2
```

## Development

### Type Checking

```bash
mypy git-ai-summary.py
```

### Testing

```bash
pytest tests/
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
