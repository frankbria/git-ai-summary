# Architecture & Design Decisions

## Overview

This document explains the architectural decisions, design patterns, and rationale behind git-ai-summary's implementation.

**Current Version**: v1.0
**Architecture Style**: Monolithic (single-file) with provider abstraction
**Target Architecture** (v1.2+): Modular with clean separation of concerns

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Design Patterns](#design-patterns)
3. [Component Breakdown](#component-breakdown)
4. [Configuration System](#configuration-system)
5. [Provider Abstraction](#provider-abstraction)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Extensibility Points](#extensibility-points)
8. [Future Architecture Evolution](#future-architecture-evolution)
9. [Design Decision Log](#design-decision-log)

---

## High-Level Architecture

### Current Architecture (v1.0)

```
┌─────────────────────────────────────────────────────────────┐
│                     git-ai-summary.py                       │
│                      (Single File)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   CLI       │  │  Config      │  │  Git Utils     │   │
│  │   (main)    │─▶│  Loading     │  │  (commands)    │   │
│  └─────────────┘  └──────────────┘  └────────────────┘   │
│         │                                    │             │
│         ▼                                    ▼             │
│  ┌─────────────────────────────────────────────────┐      │
│  │         Prompt Engineering                      │      │
│  │   (create_ai_prompt, focus modes)               │      │
│  └─────────────────────────────────────────────────┘      │
│         │                                                  │
│         ▼                                                  │
│  ┌─────────────────────────────────────────────────┐      │
│  │         Provider Factory                        │      │
│  │          (make_provider)                        │      │
│  └─────────────────────────────────────────────────┘      │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Provider Implementations                  │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ OpenAI │ Anthropic │ Ollama │ OpenRouter │ Gemini │ │ │
│  │ Cohere │ Mistral   │ LiteLLM│ LLM CLI              │ │
│  └──────────────────────────────────────────────────────┘ │
│         │                                                  │
│         ▼                                                  │
│  ┌─────────────────────────────────────────────────┐      │
│  │        Retry Logic & HTTP Handling              │      │
│  │   (_make_request_with_retry)                    │      │
│  └─────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Dependencies                      │
├─────────────────────────────────────────────────────────────┤
│  • Git (subprocess)                                         │
│  • AI Provider APIs (HTTP/requests)                         │
│  • Clipboard (pbcopy/xclip)                                 │
│  • File System (.env, output files)                         │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (v1.2+)

```
git-ai-summary/
├── cli/
│   ├── __init__.py
│   ├── main.py              # CLI interface, argparse
│   └── commands.py          # Command handlers (health-check, dry-run)
│
├── core/
│   ├── __init__.py
│   ├── config.py            # Configuration loading & validation
│   ├── git_integration.py   # Git command execution
│   ├── prompt.py            # Prompt engineering
│   └── retry.py             # Retry decorator (reusable)
│
├── providers/
│   ├── __init__.py
│   ├── base.py              # Provider Protocol
│   ├── factory.py           # Provider factory
│   ├── openai.py            # OpenAI implementation
│   ├── anthropic.py         # Anthropic implementation
│   └── ...                  # Other providers
│
├── utils/
│   ├── __init__.py
│   ├── logging.py           # Structured logging
│   └── clipboard.py         # Clipboard integration
│
└── git-ai-summary.py        # Entry point (imports from above)
```

**Why deferred to v1.2?** Current single-file design is manageable at ~1000 LOC. Will modularize when approaching ~2000 LOC to prevent complexity.

---

## Design Patterns

### 1. Protocol Pattern (Structural Typing)

**Pattern**: Provider abstraction using Python Protocol (PEP 544)

**Implementation**:
```python
from typing import Protocol

class AIProvider(Protocol):
    """Protocol for AI provider implementations."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate AI response from prompts."""
        ...
```

**Benefits**:
- No inheritance required (duck typing)
- Easy to add new providers
- Clear interface contract
- Type checking support (mypy)

**Trade-offs**:
- Runtime checks not enforced (relies on type checker)
- Protocol methods can't share implementation (no base class)

**Decision Rationale**: Chosen for flexibility. Adding a new AI provider only requires implementing `generate()` method, no inheritance overhead.

---

### 2. Factory Pattern

**Pattern**: Provider factory function

**Implementation**:
```python
def make_provider(config: Config, logger: logging.Logger) -> AIProvider:
    """Factory function to create appropriate AI provider."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        # ... 9 total providers
    }

    provider_class = providers.get(config.provider)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {config.provider}")

    return provider_class(config, logger)
```

**Benefits**:
- Single point of provider instantiation
- Easy to add new providers (register in dict)
- Hides implementation details from caller

**Trade-offs**:
- All providers must be imported upfront (no lazy loading)

**Decision Rationale**: Simplicity. 9 providers is manageable. If we grow to 50+ providers, we'd switch to plugin-based lazy loading.

---

### 3. Dataclass Pattern

**Pattern**: Configuration as immutable dataclass

**Implementation**:
```python
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration for AI providers and global settings."""
    provider: ProviderType
    model: Optional[str]
    # ... 30+ configuration fields
```

**Benefits**:
- Type safety for all config fields
- Auto-generated `__init__`, `__repr__`, `__eq__`
- IDE autocomplete support
- Immutable (frozen=True could be added)

**Trade-offs**:
- Verbose (30+ fields listed explicitly)
- No dynamic fields

**Decision Rationale**: Explicitness over magic. We want type safety and clear documentation of all configuration options.

---

### 4. Retry Decorator Pattern (Future)

**Pattern**: Separate retry logic from business logic

**Current** (v1.0):
```python
# Retry logic embedded in _make_request_with_retry()
def _make_request_with_retry(url, headers, data, timeout, max_retries, logger):
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(...)
            # Handle 429, 5xx, timeouts, etc.
        except:
            # Retry logic
```

**Proposed** (v1.2):
```python
# Retry logic as decorator
@with_retry(max_retries=3, backoff=ExponentialBackoff())
def make_http_request(url, headers, data, timeout):
    return requests.post(url, headers=headers, json=data, timeout=timeout)
```

**Benefits**:
- Separates concerns (retry vs HTTP)
- Reusable across different operations
- Easier to test retry logic independently

**Decision Rationale**: Deferred to v1.2. Current approach works, but will refactor when adding new retry-able operations (e.g., git commands).

---

## Component Breakdown

### 1. Configuration System (`load_config()`)

**Responsibility**: Load and validate configuration from environment

**Design**:
- **Search Path**: 4-level hierarchy (current dir → git root → home → install dir)
- **Validation**: API key presence checked at load time
- **Immutability**: Config object is read-only after creation

**Key Code**:
```python
def load_config(provider: Optional[str] = None, model: Optional[str] = None) -> Config:
    """Load configuration from environment and CLI arguments."""
    # 1. Search for .env file in hierarchy
    # 2. Load environment variables
    # 3. Validate provider and API keys
    # 4. Return immutable Config object
```

**Design Decisions**:
- **Why 4-level search?** Supports global config (~/.config) with project overrides (./env)
- **Why fail-fast on missing API key?** Better to fail at startup than after processing commits
- **Why not use ConfigParser?** .env format is simpler, widely used (Docker, Heroku)

---

### 2. Git Integration (`get_commits_since()`)

**Responsibility**: Execute git commands and parse output

**Design**:
- **Subprocess-based**: Uses `subprocess.run()` for git commands
- **Error Handling**: Captures stderr, returns empty list on failure
- **Diff Truncation**: Limits diffs to 5000 chars to prevent prompt bloat

**Key Code**:
```python
def get_commits_since(since_ref="HEAD~10", until_ref="HEAD"):
    """Get commits with their diffs."""
    # 1. Get commit hashes via git rev-list
    # 2. For each commit, get metadata via git show
    # 3. For each commit, get diff via git diff
    # 4. Truncate large diffs
    # 5. Return list of commit dicts
```

**Design Decisions**:
- **Why subprocess instead of GitPython?** Minimizes dependencies (only python-dotenv, requests)
- **Why truncate at 5000 chars?** Balance between context and token cost
- **Why not use git log --format?** Easier to parse separately (show for metadata, diff for changes)

---

### 3. Prompt Engineering (`create_ai_prompt()`)

**Responsibility**: Generate structured prompts for AI analysis

**Design**:
- **Focus Modes**: Features, security, performance (different emphasis)
- **Diff Filtering**: Extracts relevant code changes, ignores noise
- **Structured Format**: Clear sections (commits, metadata, diffs)

**Key Code**:
```python
def create_ai_prompt(commits, focus="features"):
    """Create a structured prompt for AI analysis."""
    # 1. Generate focus-specific instructions
    # 2. For each commit:
    #    - Add metadata (author, timestamp, message)
    #    - Add file stats
    #    - Filter diff for relevant changes
    # 3. Return formatted prompt string
```

**Design Decisions**:
- **Why focus modes?** Different use cases (sprint review vs security audit)
- **Why filter diffs?** Raw diffs contain noise (whitespace, generated files)
- **Why structured format?** Consistent input → consistent output from AI

---

### 4. Provider Implementations

**Responsibility**: Translate prompts to provider-specific API calls

**Design**:
- **Uniform Interface**: All providers implement `generate(system_prompt, user_prompt)`
- **Provider-Specific Details**: Headers, request format, response parsing
- **Error Mapping**: Provider errors → user-friendly messages

**Example: Anthropic Provider**:
```python
class AnthropicProvider:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.anthropic_model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.anthropic_base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }
        data = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 2048
        }

        response = _make_request_with_retry(url, headers, data, ...)
        result = response.json()
        return result["content"][0]["text"]
```

**Design Decisions**:
- **Why pass entire Config?** Providers need multiple fields (API key, model, base URL)
  - *Note*: v1.2 will use `ProviderConfig` for Interface Segregation Principle
- **Why separate provider classes?** Each API has unique request/response format
- **Why not use LangChain?** Want minimal dependencies, full control over prompts

---

### 5. Retry Logic (`_make_request_with_retry()`)

**Responsibility**: Handle transient failures with exponential backoff

**Design**:
- **Retryable Errors**: HTTP 429 (rate limit), HTTP 5xx (server error), timeouts
- **Non-Retryable Errors**: HTTP 401/403 (auth), HTTP 4xx (client error)
- **Backoff Strategy**: Exponential (1s, 2s, 4s, 8s, ...)

**Key Code**:
```python
def _make_request_with_retry(url, headers, data, timeout, max_retries, logger):
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=timeout)

            # Fail-fast on auth errors
            if response.status_code in (401, 403):
                raise ValueError("Authentication failed")

            # Retry on rate limit or server error
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                continue
            raise ValueError("Request timed out")
```

**Design Decisions**:
- **Why exponential backoff?** Industry standard, prevents thundering herd
- **Why max 3 retries?** Balance between reliability and user wait time
- **Why no retry on 401?** Auth errors won't fix themselves, fail fast

---

## Configuration System

### Search Path Hierarchy

**Priority** (first found wins):
1. **Current Directory** (`./.env`)
   - Use case: Project-specific overrides
   - Example: Use different provider for work vs personal projects

2. **Git Repository Root** (`$(git rev-parse --show-toplevel)/.env`)
   - Use case: Repository-wide settings
   - Example: Shared team configuration (can be in git or .gitignore)

3. **User Global Config** (`~/.config/git-ai-summary/.env`)
   - Use case: Default user settings across all projects
   - Example: Personal API keys, preferred provider

4. **Installation Directory** (`/path/to/git-ai-summary/.env`)
   - Use case: Fallback defaults
   - Example: System-wide installation for multiple users

**Design Rationale**:
- **Why 4 levels?** Balances flexibility (project overrides) with convenience (global defaults)
- **Why not XDG_CONFIG_HOME?** `~/.config` is effectively XDG_CONFIG_HOME on most systems
- **Why not ~/.git-ai-summary?** Prefer XDG standard (~/.config/)

### Configuration Override Rules

**Priority** (highest to lowest):
1. CLI arguments (`--provider`, `--model`)
2. Environment variable from .env file
3. Default value in Config dataclass

**Example**:
```bash
# .env file:
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-latest

# CLI:
./git-ai-summary.py --provider openai --model gpt-4o

# Result:
# provider = "openai" (CLI override)
# model = "gpt-4o" (CLI override)
# (ANTHROPIC_MODEL ignored because provider changed)
```

---

## Provider Abstraction

### Why Protocol Over Abstract Base Class?

**Protocol** (chosen):
```python
class AIProvider(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...
```

**Abstract Base Class** (alternative):
```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass
```

**Decision**: Protocol chosen because:
- ✅ No inheritance required (simpler for contributors)
- ✅ Duck typing (if it quacks like a provider, it is one)
- ✅ Easier to mock in tests
- ❌ No runtime enforcement (type checker only)

---

### Provider Lifecycle

**Current** (v1.0):
```
1. User runs command with --provider flag
2. load_config() validates API key exists
3. make_provider() instantiates provider class
4. provider.generate() called once per analysis
5. Provider object discarded after use
```

**Future** (v1.2):
```
1. User runs command
2. Health check: provider.health_check() (NEW)
3. Analysis: provider.generate()
4. Cleanup: provider.cleanup() (NEW)
```

**New Methods**:
- `health_check() -> bool`: Verify API key, connectivity, model availability
- `cleanup() -> None`: Close connections, cleanup resources

---

## Error Handling Strategy

### Error Categories

1. **User Errors** (actionable, don't retry)
   - Missing API key → Show how to set it
   - Invalid provider → Show list of valid providers
   - No commits in range → Explain how to adjust range

2. **Transient Errors** (retry with backoff)
   - HTTP 429 (rate limit) → Retry with exponential backoff
   - HTTP 5xx (server error) → Retry
   - Timeout → Retry

3. **Permanent Errors** (fail-fast, don't retry)
   - HTTP 401/403 (auth) → Check API key
   - HTTP 404 (not found) → Check endpoint URL
   - Invalid JSON response → Provider API changed

### Error Message Philosophy

**Principles**:
1. **User-Friendly**: Explain what went wrong in plain language
2. **Actionable**: Tell user how to fix it
3. **Context-Rich**: Include correlation ID for support
4. **Non-Leaky**: Never expose API keys or sensitive data

**Example Error Messages**:
```python
# Good:
"""
Error: Failed to connect to Anthropic API

Possible causes:
  1. ANTHROPIC_API_KEY is invalid
     → Verify key at https://console.anthropic.com/
     → Current key: sk-ant-***...4Tq9

  2. Network connectivity issue
     → Test: curl https://api.anthropic.com/v1/messages

  3. Anthropic API is down
     → Check status: https://status.anthropic.com/

Correlation ID: a1b2c3d4-5678-90ab-cdef-1234567890ab
For support: https://github.com/user/repo/issues
"""

# Bad:
"""
Error: HTTP 401
"""
```

---

## Extensibility Points

### 1. Adding a New AI Provider

**Steps**:
```python
# 1. Create provider class implementing AIProvider protocol
class NewProvider:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.new_provider_model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Implement API call logic
        pass

# 2. Add to provider factory
def make_provider(config: Config, logger: logging.Logger) -> AIProvider:
    providers = {
        # ... existing providers
        "new_provider": NewProvider,  # ADD THIS
    }

# 3. Add to ProviderType Literal
ProviderType = Literal["openai", "anthropic", ..., "new_provider"]  # ADD HERE

# 4. Add configuration fields to Config dataclass
@dataclass
class Config:
    # ... existing fields
    new_provider_api_key: Optional[str]  # ADD THIS
    new_provider_model: str             # ADD THIS
    new_provider_base_url: str          # ADD THIS

# 5. Add to load_config() validation
validation_map = {
    # ... existing validations
    "new_provider": (config.new_provider_api_key, "NEW_PROVIDER_API_KEY"),
}

# 6. Update README.md, .env.example, CLI help text
```

**Effort**: ~100 LOC, ~1 hour for experienced contributor

---

### 2. Adding a New Focus Mode

**Steps**:
```python
# 1. Update create_ai_prompt() to handle new focus
def create_ai_prompt(commits, focus="features"):
    if focus == "features":
        instructions = "Focus on new features..."
    elif focus == "security":
        instructions = "Focus on security implications..."
    elif focus == "new_focus":  # ADD THIS
        instructions = "Focus on X, Y, Z..."

# 2. Update CLI choices
parser.add_argument('--focus',
    default='features',
    choices=['features', 'security', 'performance', 'new_focus'],  # ADD HERE
    help='Analysis focus'
)
```

**Effort**: ~20 LOC, ~15 minutes

---

### 3. Adding a New Output Format

**Current**: Plain text output to stdout or file

**Future**: JSON, Markdown, HTML

**Extension Point**:
```python
# Add formatter abstraction
class OutputFormatter(Protocol):
    def format(self, analysis: str, metadata: dict) -> str: ...

class PlainTextFormatter:
    def format(self, analysis: str, metadata: dict) -> str:
        return f"=== Analysis ===\n{analysis}"

class JSONFormatter:
    def format(self, analysis: str, metadata: dict) -> str:
        return json.dumps({"analysis": analysis, **metadata})

# Use in main()
formatter = make_formatter(args.format)
output = formatter.format(response, metadata={"provider": "anthropic", ...})
print(output)
```

---

## Future Architecture Evolution

### v1.1: Enhanced Observability (No Structural Changes)
- Add `--health-check`, `--dry-run`, `--validate-config` commands
- Add structured JSON logging
- Remain single-file architecture

### v1.2: Modularization
- Split into modules (see Target Architecture above)
- Refactor retry logic to decorator
- Introduce `ProviderConfig` (Interface Segregation)
- Add provider lifecycle methods (`health_check()`, `cleanup()`)

### v2.0: Plugin System (Future)
- Provider auto-discovery via entry points
- Lazy loading of providers
- Third-party provider plugins (installed via pip)

**Example Plugin System**:
```python
# setup.py for third-party provider
setup(
    name="git-ai-summary-custom-provider",
    entry_points={
        "git_ai_summary.providers": [
            "custom = my_package:CustomProvider"
        ]
    }
)

# Auto-discovery in git-ai-summary
import pkg_resources

def discover_providers():
    providers = {}
    for entry_point in pkg_resources.iter_entry_points('git_ai_summary.providers'):
        providers[entry_point.name] = entry_point.load()
    return providers
```

---

## Design Decision Log

### ADR-001: Single-File vs Modular Architecture

**Date**: 2025-10-22
**Status**: Accepted (for v1.0), Will Refactor (v1.2)

**Context**: Should we split into modules or keep single file?

**Decision**: Single file for v1.0, modularize in v1.2 when LOC > 1500

**Rationale**:
- ✅ Simple to install (just copy one file)
- ✅ Easy to understand for newcomers (all code in one place)
- ✅ No import path issues
- ❌ Harder to test individual components
- ❌ Will become unwieldy >2000 LOC

**Consequences**: When approaching 1500 LOC, refactor to modular architecture per Target Architecture section.

---

### ADR-002: Protocol vs Abstract Base Class for Providers

**Date**: 2025-10-22
**Status**: Accepted

**Context**: How to enforce provider interface?

**Decision**: Use Protocol (structural typing)

**Rationale**:
- Simpler for contributors (no inheritance)
- Easier to mock in tests
- Pythonic (duck typing)

**Consequences**: Type checking with mypy recommended, but not enforced at runtime.

---

### ADR-003: Configuration Hierarchy (4 Levels)

**Date**: 2025-10-22
**Status**: Accepted

**Context**: How many configuration levels to support?

**Decision**: 4 levels (current dir → git root → home → install)

**Rationale**:
- Supports project-specific overrides
- Supports team/repo configuration
- Supports user global defaults
- Balances flexibility with simplicity

**Consequences**: Must document clearly to avoid user confusion.

---

### ADR-004: Retry Logic Embedded vs Decorator

**Date**: 2025-10-22
**Status**: Accepted (embedded for v1.0), Refactor (v1.2)

**Context**: Should retry logic be embedded in HTTP function or separate decorator?

**Decision**: Embedded for v1.0, refactor to decorator in v1.2

**Rationale**:
- Embedded is simpler to understand initially
- Decorator is more reusable and testable
- Can refactor when adding more retry-able operations

**Consequences**: Technical debt to refactor in v1.2.

---

### ADR-005: Minimum Dependencies

**Date**: 2025-10-22
**Status**: Accepted

**Context**: Should we use GitPython, LangChain, or other libraries?

**Decision**: Minimize dependencies (only python-dotenv, requests)

**Rationale**:
- Easier to install (fewer dependencies)
- Smaller attack surface (security)
- More control over behavior
- Faster startup time

**Consequences**: Must implement git parsing, HTTP retry logic ourselves.

---

### ADR-006: Diff Truncation at 5000 Characters

**Date**: 2025-10-22
**Status**: Accepted

**Context**: How to handle large diffs (100KB+ per commit)?

**Decision**: Truncate at 5000 characters per commit

**Rationale**:
- Balances context (enough for AI) vs cost (token usage)
- 5000 chars ≈ 1200 tokens (reasonable for most commits)
- Prevents prompt bloat on refactoring commits

**Consequences**:
- May miss important changes in large commits
- Users can override via environment variable (future: `AI_MAX_DIFF_SIZE`)

---

## Appendix: Code Metrics

**Current (v1.0)**:
- Total lines: ~960 LOC
- Functions: 12
- Classes: 10 (9 providers + 1 Protocol)
- Complexity: Low-Medium (most functions <50 LOC)

**Projected (v1.2)**:
- Total lines: ~1500 LOC
- Modules: 10+ files
- Functions: ~30
- Classes: ~15
- Complexity: Medium (modular, but more files)

---

## References

- [REQUIREMENTS.md](REQUIREMENTS.md) - Functional/non-functional requirements
- [PRD.md](PRD.md) - Product roadmap
- [CLAUDE.md](CLAUDE.md) - Developer guide
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/) - Python Protocol spec
- [Twelve-Factor App](https://12factor.net/) - Configuration best practices
