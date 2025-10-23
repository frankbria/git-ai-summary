# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-22

### Added - Sprint 2: Observability & Validation

- **--health-check**: Comprehensive configuration and connectivity verification
  - Validates configuration file loading
  - Checks provider and model settings
  - Verifies API key presence and format
  - Tests network connectivity to provider endpoints
  - Validates Ollama model availability for local installations
  - Returns exit code 0 on success, 1 on failure

- **--validate-config**: Configuration validation without network calls
  - Validates provider selection against supported providers
  - Checks required API keys for each provider
  - Verifies model configuration
  - Validates base URLs (HTTP/HTTPS)
  - Checks timeout and retry settings
  - Validates log level settings
  - Provides warnings for non-critical issues
  - Returns detailed error/warning counts

- **--dry-run**: Preview prompts and estimate costs before making API calls
  - Shows exact prompt that would be sent to AI
  - Estimates input token count (4 chars/token approximation)
  - Estimates output tokens (default 500, typical for analysis)
  - Calculates estimated cost based on provider pricing
  - Supports all 9 providers with comprehensive pricing data
  - No API calls made in dry-run mode
  - Displays prompt length in characters

- **--version** (`-v`): Display version information
  - Shows current version (1.1.0)
  - Standard --version flag behavior

- **Provider Pricing Module**: Comprehensive pricing data for cost estimation
  - **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-4, GPT-3.5-turbo
  - **Anthropic**: Claude 3.5 Sonnet (all versions), Claude 3 Opus, Claude 3 Haiku, Claude 4.5 Sonnet
  - **Google Gemini**: Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 1.0 Pro
  - **Cohere**: Command R+, Command R, Command, Command Light
  - **Mistral**: Mistral Large, Medium, Small, Open Mistral 7B
  - **OpenRouter**: Common model pricing (Claude, GPT-4o, Gemini)
  - **Free providers**: Ollama (local), LiteLLM (proxy), LLM CLI
  - Pricing per million tokens (input/output separate)
  - `estimate_token_count()`: Rough token estimation
  - `estimate_cost()`: Cost calculation with pricing lookup

### Changed

- **Version**: Bumped from 1.0.0 to 1.1.0
- **README.md**: Added "Diagnostic Commands (v1.1)" section with examples
- **Features list**: Updated with 4 new v1.1 features

### Technical Details

- **Code additions**:
  - `git-ai-summary.py`: 961 → 1,438 lines (+477 lines, +50%)
  - New `health_check()` function: 215 lines
  - New `validate_config()` function: 134 lines
  - New pricing module: 84 lines (pricing data + helper functions)
  - 4 new CLI arguments

- **Pricing data coverage**:
  - 41 model configurations across 9 providers
  - Input/output token pricing per million tokens
  - Graceful fallback for unknown models

### Testing

- Tested --health-check with Anthropic provider (4 checks passed)
- Tested --validate-config with Anthropic provider (8 checks passed, 0 errors)
- Tested --dry-run with cost estimation (estimated $0.012507 for 1,669 input tokens)
- Tested --version flag (displays "git-ai-summary 1.1.0")

## [2.0.0] - Multi-Provider Support

### Added

#### Core Features
- **Multi-provider architecture** supporting 9 AI providers:
  - OpenAI (GPT models)
  - Anthropic (Claude models)
  - Local Ollama
  - OpenRouter
  - Google Gemini
  - Cohere
  - Mistral AI
  - LiteLLM (with python/http/cli modes)
  - LLM CLI (Simon Willison's tool)

- **Environment-based configuration** using `.env` files
  - Secure API key management
  - Provider-specific settings (models, base URLs)
  - Global configuration (timeouts, retries, logging)
  - CLI argument overrides

- **Robust error handling and retry logic**
  - Automatic retry with exponential backoff
  - Rate limit handling (HTTP 429)
  - Authentication error detection (HTTP 401/403)
  - Connection error recovery
  - Timeout management

- **Structured logging with correlation IDs**
  - Request tracking across retries
  - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
  - Duration tracking for AI requests

- **Type-safe configuration**
  - Type hints throughout the codebase
  - Dataclass-based configuration
  - Protocol-based provider interface
  - Input validation with descriptive errors

#### New CLI Arguments
- `--provider`: Choose AI provider (overrides .env)
- `--model`: Override model selection (overrides .env)
- `--output-copy`: Copy AI analysis to clipboard (new in v2.0)

#### New Configuration Files
- `.env.example`: Template with all configuration options
- `requirements.txt`: Python dependencies
- `.gitignore`: Protect sensitive files
- `README.md`: Comprehensive documentation
- `CHANGELOG.md`: This file
- `CLIPBOARD_GUIDE.md`: Detailed clipboard and output options guide

### Changed

#### Breaking Changes
- **Removed** `--claude-api-key` argument (replaced by `--provider` + `.env` configuration)
- API keys now managed via environment variables instead of CLI arguments

#### Improvements
- Refactored prompt handling to separate system and user prompts
- Enhanced clipboard integration with dual functionality:
  - `--copy`: Copies **prompt** for manual AI input (e.g., ChatGPT web UI)
  - `--output-copy`: Copies **AI analysis** for sharing/pasting
- `--output` now correctly saves analysis (not prompt) when using AI provider
- Better error messages with actionable guidance
- Provider-specific error handling and retry strategies

### Technical Details

#### Architecture
- **Strategy Pattern**: Provider implementations via factory pattern
- **Dependency Injection**: Providers receive Config and Logger
- **Single Responsibility**: Each provider class handles one AI service
- **Protocol-based Design**: AIProvider protocol for consistency

#### Security
- API keys never logged or exposed in error messages
- Environment variable-based secret management
- .env files excluded from version control
- Secure subprocess handling for CLI providers

#### Performance
- Configurable timeouts (default: 30s)
- Retry with exponential backoff (default: 2 retries)
- Request duration tracking
- Correlation IDs for distributed tracing

### Migration Guide

#### From v1.x to v2.0

**Before (v1.x):**
```bash
./git-ai-summary.py --claude-api-key sk-ant-...
```

**After (v2.0):**

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Add your API key:
```env
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_AI_PROVIDER=anthropic
```

3. Run with provider:
```bash
./git-ai-summary.py --provider anthropic
```

#### Configuration Mapping

| v1.x | v2.0 |
|------|------|
| `--claude-api-key` | `.env`: `ANTHROPIC_API_KEY` + `--provider anthropic` |
| N/A | `.env`: `DEFAULT_AI_PROVIDER` |
| N/A | `--model` for model override |

### Dependencies

New dependencies added:
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.31.0` - HTTP client for API calls

Optional dependencies (provider-specific):
- `litellm` - For LiteLLM python mode
- `llm` - For LLM CLI provider

### Documentation

- Comprehensive README with usage examples for all providers
- Provider-specific configuration guides
- Troubleshooting section
- Advanced configuration options
- Development setup instructions

### Testing Recommendations

Before deploying, test with your chosen provider(s):

```bash
# Test OpenAI
./git-ai-summary.py --provider openai --model gpt-4o-mini

# Test Anthropic
./git-ai-summary.py --provider anthropic

# Test local Ollama
./git-ai-summary.py --provider ollama

# Test with custom model
./git-ai-summary.py --provider openai --model gpt-4
```

### Future Enhancements

Potential improvements for future versions:
- Unit tests with pytest
- Type checking with mypy
- Integration tests for each provider
- Provider health checks
- Caching layer for repeated requests
- Streaming support for long responses
- Async/await for concurrent requests
- Cost tracking per provider
- Response quality metrics
