# Requirements Specification

## Document Information

**Version**: 1.0
**Last Updated**: 2025-10-22
**Status**: Draft
**Authors**: Expert Panel Review (Wiegers, Nygard, Fowler, Crispin, Hightower)

---

## 1. Functional Requirements

### FR-001: Multi-Provider AI Support
**Priority**: P0 (Critical)
**Status**: ✅ Implemented

The system SHALL support multiple AI providers with consistent interface:
- OpenAI (GPT models)
- Anthropic (Claude models)
- Google Gemini
- Cohere
- Mistral AI
- OpenRouter (aggregator)
- Ollama (local models)
- LiteLLM (proxy/CLI/Python)
- LLM CLI (Simon Willison's tool)

**Acceptance Criteria**:
- User can switch providers via `--provider` flag
- Each provider uses consistent Protocol interface
- Configuration supports provider-specific settings
- Error messages are provider-specific and actionable

---

### FR-002: Git Commit Analysis
**Priority**: P0 (Critical)
**Status**: ✅ Implemented

The system SHALL analyze git commit history and generate AI summaries:
- Extract commits within specified range (`--since`, `--until`)
- Parse commit metadata (author, timestamp, message, diff)
- Generate structured prompts for AI analysis
- Support focus modes (features, security, performance)

**Acceptance Criteria**:
- Commits are parsed with full metadata
- Diffs are truncated at configurable limit (currently 5000 chars)
- Auto-detection of recent sync points works via reflog
- Output is formatted for readability

---

### FR-003: Configuration Hierarchy
**Priority**: P0 (Critical)
**Status**: ✅ Implemented

The system SHALL search for `.env` configuration in priority order:
1. Current directory (`.env`)
2. Git repository root (`.env`)
3. User global config (`~/.config/git-ai-summary/.env`)
4. Installation directory (`.env`)

**Acceptance Criteria**:
- First found `.env` file is used exclusively
- CLI arguments override environment variables
- Configuration loading is logged at DEBUG level
- Missing required API keys fail with clear error messages

---

### FR-004: Health Check Command
**Priority**: P1 (High)
**Status**: ❌ Not Implemented

The system SHALL provide a `--health-check` command that verifies:
- Configuration file is found and loadable
- API key is present for selected provider
- Network connectivity to provider endpoint
- Model availability for selected provider

**Acceptance Criteria**:
```bash
$ ./git-ai-summary.py --health-check
✓ Configuration loaded from: ~/.config/git-ai-summary/.env
✓ Provider: anthropic
✓ API Key: present (sk-ant-***...ending 4Tq9)
✓ Connectivity: SUCCESS (162ms)
✓ Model available: claude-3-5-sonnet-latest
System Status: HEALTHY
```

**Example: Failure Case**:
```bash
$ ./git-ai-summary.py --health-check
✓ Configuration loaded from: ./.env
✓ Provider: anthropic
✗ API Key: missing or invalid
✗ Connectivity: FAILED (Connection refused)
System Status: UNHEALTHY

Troubleshooting:
- Set ANTHROPIC_API_KEY in .env file
- Verify API key at https://console.anthropic.com/
- Check network connectivity
```

---

### FR-005: Dry-Run Mode with Cost Estimation
**Priority**: P1 (High)
**Status**: ❌ Not Implemented

The system SHALL provide `--dry-run` mode that:
- Analyzes commits without making API calls
- Estimates token count for prompt
- Estimates cost based on provider pricing
- Shows what would be analyzed

**Acceptance Criteria**:
```bash
$ ./git-ai-summary.py --dry-run --provider anthropic --since HEAD~10
Analysis Plan:
  Commits to analyze: 8
  Prompt size: 3,247 characters
  Estimated tokens: ~4,500 input tokens
  Estimated cost: $0.02 USD (Anthropic pricing)
  Provider: anthropic
  Model: claude-3-5-sonnet-latest

[No API call made. Remove --dry-run to execute.]
```

---

### FR-006: Configuration Validation Command
**Priority**: P1 (High)
**Status**: ❌ Not Implemented

The system SHALL provide `--validate-config` command that:
- Checks all configuration files in search path
- Validates syntax and required fields
- Reports conflicts or issues
- Does not make network calls

**Acceptance Criteria**:
```bash
$ ./git-ai-summary.py --validate-config
Configuration Search Results:
  1. ./.env - FOUND
     ✓ DEFAULT_AI_PROVIDER=anthropic
     ✓ ANTHROPIC_API_KEY=sk-ant-*** (present)
     ✓ ANTHROPIC_MODEL=claude-3-5-sonnet-latest
     ⚠ OPENAI_API_KEY not set (optional)

  2. ~/.config/git-ai-summary/.env - FOUND (not used)
     Note: Overridden by ./.env in current directory

Configuration: VALID
Provider: anthropic (ready)
```

---

### FR-007: Version Information
**Priority**: P2 (Medium)
**Status**: ❌ Not Implemented

The system SHALL provide `--version` flag showing:
- Tool version number
- Python version used
- Installed provider package versions

**Acceptance Criteria**:
```bash
$ ./git-ai-summary.py --version
git-ai-summary version 1.0.0
Python 3.12.0
Dependencies:
  - python-dotenv 1.0.0
  - requests 2.31.0
```

---

## 2. Non-Functional Requirements

### NFR-001: Performance Limits
**Priority**: P0 (Critical)
**Status**: ⚠️ Partially Defined

**Maximum Diff Size**:
- MUST truncate diffs at 5,000 characters per commit
- SHALL log when truncation occurs
- SHOULD be configurable via environment variable `AI_MAX_DIFF_SIZE`

**Maximum Commits Per Analysis**:
- SHOULD warn when analyzing >50 commits
- SHOULD allow override with `--force` flag
- MUST prevent analysis of >200 commits without explicit confirmation

**Request Timeout**:
- DEFAULT timeout: 30 seconds (configurable via `AI_TIMEOUT_SECONDS`)
- MUST fail gracefully on timeout with clear error message
- SHALL include correlation ID in timeout errors

**Example**:
```bash
$ ./git-ai-summary.py --since HEAD~100
Warning: Analyzing 87 commits may take several minutes and incur significant API costs.
Estimated cost: $0.45 USD
Continue? [y/N]: _
```

---

### NFR-002: Reliability & Error Recovery
**Priority**: P1 (High)
**Status**: ⚠️ Partially Implemented

**Retry Logic**:
- MUST retry on HTTP 429 (rate limit) with exponential backoff
- MUST retry on HTTP 5xx (server errors) with exponential backoff
- Default max retries: 3 (configurable via `AI_MAX_RETRIES`)
- Backoff schedule: 1s, 2s, 4s, 8s, ...

**Partial Failure Handling**:
- ❌ NOT IMPLEMENTED: Resume capability
- SHOULD save successfully analyzed commits before failure
- SHOULD allow resuming from last successful commit
- MUST log correlation ID for failed requests

**Example Desired Behavior**:
```bash
$ ./git-ai-summary.py --provider anthropic --since HEAD~20
Analyzing commit 1/20... ✓
Analyzing commit 2/20... ✓
...
Analyzing commit 15/20... ✗ Timeout after 30s

Partial results saved to: git-ai-summary-partial.md
Correlation ID: a1b2c3d4-5678-90ab-cdef-1234567890ab

To resume from commit 15:
  ./git-ai-summary.py --resume a1b2c3d4
```

---

### NFR-003: Security Requirements
**Priority**: P1 (High)
**Status**: ⚠️ Needs Improvement

**API Key Storage**:
- CURRENT: API keys stored in plaintext `.env` files
- SHOULD document security implications in README
- SHOULD recommend OS-level keychain integration (future enhancement)
- MUST never log API keys (even at DEBUG level)

**API Key Validation**:
- MUST validate key format before making API calls
- MUST distinguish between "missing key" vs "invalid key" errors
- SHOULD mask API keys in error messages (show first/last 4 chars only)

**Example Error Messages**:
```bash
# Good:
Error: ANTHROPIC_API_KEY is missing. Set it in .env file.

# Good:
Error: ANTHROPIC_API_KEY appears invalid (sk-ant-***...4Tq9)
Response: 401 Unauthorized

# Bad (never do this):
Error: Invalid API key: sk-ant-1234567890abcdef...
```

**Audit Logging**:
- MUST log all API requests with correlation ID
- SHOULD log timestamp, provider, model, prompt size
- MUST NOT log prompt content or API responses (may contain sensitive data)

---

### NFR-004: Observability
**Priority**: P1 (High)
**Status**: ⚠️ Partially Implemented

**Structured Logging**:
- CURRENT: Human-readable logs with correlation IDs
- SHOULD support JSON-formatted logs (via `--log-format json`)
- MUST include correlation ID in all log entries
- SHOULD log request/response timing

**Example JSON Log Format**:
```json
{
  "timestamp": "2025-10-22T17:45:23.123Z",
  "level": "INFO",
  "correlation_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "event": "api_request",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-latest",
  "prompt_size": 3247,
  "estimated_tokens": 4500
}
```

**Metrics Collection** (Future):
- Success rate per provider
- Latency percentiles (p50, p95, p99)
- Error rate by error type
- Cost per analysis session

---

### NFR-005: Usability
**Priority**: P1 (High)
**Status**: ⚠️ Needs Improvement

**Installation Success Rate**:
- Target: >95% of users complete installation without issues
- MUST validate prerequisites before installation
- MUST provide actionable error messages
- SHOULD auto-detect shell type for PATH modification

**Error Message Quality**:
- MUST include correlation ID for debugging
- MUST provide next steps for resolution
- SHOULD link to relevant documentation
- MUST distinguish between user errors vs system errors

**Example Error Message Structure**:
```bash
Error: Failed to connect to Ollama at http://localhost:11434

Possible causes:
  1. Ollama is not running
     → Start Ollama: ollama serve

  2. Ollama is running on different port
     → Check port: ps aux | grep ollama
     → Update OLLAMA_BASE_URL in .env

  3. Firewall blocking connection
     → Test: curl http://localhost:11434/api/version

Correlation ID: a1b2c3d4 (use for support)
Documentation: https://github.com/user/repo#troubleshooting-ollama
```

---

### NFR-006: Testability
**Priority**: P1 (High)
**Status**: ❌ Not Implemented

**Test Coverage Target**: 80%

**Unit Test Requirements**:
- MUST test configuration loading hierarchy
- MUST test commit parsing with various git outputs
- MUST test retry logic with simulated failures
- MUST test prompt generation with different focus modes

**Integration Test Requirements**:
- MUST test provider implementations with mocked APIs
- SHOULD use VCR.py for recording/replaying API responses
- MUST test installation script in clean Docker environment

**Contract Test Requirements**:
- SHOULD validate API request/response formats for each provider
- MUST detect breaking changes in provider APIs

**Example Test Structure**:
```python
# tests/unit/test_config_loading.py
def test_config_hierarchy_current_directory_wins():
    """Current directory .env should take precedence over global config."""
    # Given: .env in current dir with provider=openai
    # Given: ~/.config/git-ai-summary/.env with provider=anthropic
    # When: load_config() is called
    # Then: config.provider == "openai"
    pass

# tests/integration/test_provider_anthropic.py
@vcr.use_cassette('fixtures/anthropic_success.yaml')
def test_anthropic_provider_success():
    """Test successful API call to Anthropic with recorded response."""
    # Uses pre-recorded API response from fixture
    pass
```

---

### NFR-007: Maintainability
**Priority**: P2 (Medium)
**Status**: ⚠️ Needs Improvement

**Code Organization**:
- CURRENT: Single-file design (git-ai-summary.py)
- SHOULD refactor into modules as complexity grows:
  - `core/config.py` - Configuration management
  - `core/git_utils.py` - Git integration
  - `core/prompt.py` - Prompt engineering
  - `core/retry.py` - Retry logic decorator
  - `providers/` - Provider implementations
  - `cli/main.py` - CLI interface

**Documentation Requirements**:
- MUST update CLAUDE.md when architecture changes
- MUST document all public APIs with docstrings
- SHOULD include examples in docstrings
- MUST keep README.md in sync with features

**Dependency Management**:
- MUST pin dependency versions in requirements.txt
- SHOULD document why each dependency is needed
- MUST test with minimum supported Python version (3.8+)

---

## 3. Quality Attributes

### Reliability
**Target**: 99% success rate for valid configurations

**Measurement**:
- Retry logic handles transient failures
- Clear error messages for permanent failures
- Correlation IDs for debugging

---

### Performance
**Target**: <5 seconds overhead (excluding AI provider latency)

**Breakdown**:
- Git command execution: <1s
- Configuration loading: <100ms
- Prompt generation: <500ms
- Provider API call: Variable (depends on provider)

---

### Security
**Target**: No API key leakage in logs or error messages

**Controls**:
- API keys masked in output (sk-ant-***...4Tq9)
- No logging of prompt content (may contain repo code)
- No logging of API responses (may contain analysis)

---

### Usability
**Target**: New user can complete analysis in <5 minutes

**Measurement**:
- Installation time: <2 minutes
- Configuration time: <2 minutes
- First analysis: <1 minute

---

## 4. Constraints

### Technical Constraints
- **Python Version**: Minimum 3.8 (for type hints and dataclasses)
- **Dependencies**: Minimize external dependencies (currently 2: python-dotenv, requests)
- **Platform**: Must work on Linux, macOS, Windows (via WSL)

### Operational Constraints
- **Installation**: Must work without root/admin privileges
- **Configuration**: Must support air-gapped environments (via Ollama)
- **Network**: Must handle offline mode gracefully (when possible)

### Legal/Licensing Constraints
- **License**: MIT (permissive open source)
- **Dependencies**: All dependencies must be MIT-compatible
- **Data Privacy**: Must not send repository code to analytics servers

---

## 5. Acceptance Criteria Summary

| Requirement ID | Description | Status | Priority | Target Version |
|----------------|-------------|--------|----------|----------------|
| FR-001 | Multi-Provider Support | ✅ Done | P0 | v1.0 |
| FR-002 | Git Commit Analysis | ✅ Done | P0 | v1.0 |
| FR-003 | Configuration Hierarchy | ✅ Done | P0 | v1.0 |
| FR-004 | Health Check Command | ❌ Needed | P1 | v1.1 |
| FR-005 | Dry-Run Mode | ❌ Needed | P1 | v1.1 |
| FR-006 | Config Validation | ❌ Needed | P1 | v1.1 |
| FR-007 | Version Info | ❌ Needed | P2 | v1.1 |
| NFR-001 | Performance Limits | ⚠️ Partial | P0 | v1.0 |
| NFR-002 | Reliability | ⚠️ Partial | P1 | v1.2 |
| NFR-003 | Security | ⚠️ Partial | P1 | v1.1 |
| NFR-004 | Observability | ⚠️ Partial | P1 | v1.1 |
| NFR-005 | Usability | ⚠️ Partial | P1 | v1.1 |
| NFR-006 | Testability | ❌ Needed | P1 | v1.2 |
| NFR-007 | Maintainability | ⚠️ Partial | P2 | v1.2 |

---

## 6. Verification & Validation

### Unit Testing
- Test configuration loading with various .env file combinations
- Test git parsing with edge cases (empty commits, merge commits, large diffs)
- Test retry logic with simulated HTTP errors
- Test prompt generation with different focus modes

### Integration Testing
- Test each provider with mocked API responses (VCR.py)
- Test installation script in clean Docker containers
- Test clipboard integration on different platforms

### User Acceptance Testing
- New user follows QUICKSTART.md without errors
- Installation completes in <5 minutes
- First analysis works without troubleshooting

### Performance Testing
- Measure overhead with 10, 50, 100 commits
- Verify timeout behavior under slow network
- Test retry logic under rate limiting

---

## 7. Glossary

| Term | Definition |
|------|------------|
| **Provider** | AI service backend (OpenAI, Anthropic, etc.) |
| **Correlation ID** | UUID for tracking individual requests through logs |
| **Dry-run** | Analyze without making API calls |
| **Health check** | Verify configuration and connectivity |
| **Focus mode** | Analysis emphasis (features, security, performance) |
| **Sync point** | Last git pull/merge commit (auto-detected) |

---

## 8. References

- [README.md](README.md) - User documentation
- [INSTALL.md](INSTALL.md) - Installation guide
- [CLAUDE.md](CLAUDE.md) - Developer guide for Claude Code
- [Expert Panel Review](./docs/expert-panel-review.md) - Specification analysis

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Expert Panel | Initial requirements based on code review |
