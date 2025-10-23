# Changelog

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
