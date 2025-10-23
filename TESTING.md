# Testing Strategy & Guide

## Overview

This document defines the comprehensive testing strategy for git-ai-summary, including test categories, coverage targets, infrastructure setup, and best practices.

**Current Status**: v1.0 has 0% test coverage
**Target for v1.1**: ≥60% coverage
**Target for v1.2**: ≥80% coverage

---

## Test Philosophy

### Testing Principles

1. **Test Pyramid**: More unit tests, fewer integration tests, minimal e2e tests
2. **Fast Feedback**: Unit tests run in <5 seconds, full suite in <30 seconds
3. **Isolated Tests**: No external dependencies (use mocking/VCR.py)
4. **Readable Tests**: Tests serve as living documentation
5. **Comprehensive Coverage**: Test happy paths, edge cases, and error conditions

### Coverage Targets by Category

```
Unit Tests:        40% coverage (core logic)
Integration Tests: 30% coverage (provider APIs, system integration)
Contract Tests:    10% coverage (API request/response formats)
E2E Tests:         5% coverage (full user workflows)
Manual Tests:      5% coverage (installation, UI/UX)
```

---

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual functions and classes in isolation

**Scope**: Core logic without external dependencies

**Tools**:
- pytest (test framework)
- pytest-mock (mocking)
- pytest-cov (coverage reporting)

**Test Structure**:
```python
# tests/unit/test_config_loading.py
import pytest
from pathlib import Path
from git_ai_summary import load_config, Config

class TestConfigLoading:
    """Test configuration loading hierarchy and validation."""

    def test_current_directory_env_takes_precedence(self, tmp_path, monkeypatch):
        """Current directory .env should override all other configs."""
        # Given: Multiple .env files in search path
        current_env = tmp_path / ".env"
        current_env.write_text("DEFAULT_AI_PROVIDER=openai\nOPENAI_API_KEY=test123")

        home_env = Path.home() / ".config" / "git-ai-summary" / ".env"
        # Mock home_env with anthropic provider...

        # When: Load configuration from current directory
        monkeypatch.chdir(tmp_path)
        config = load_config()

        # Then: Current directory config wins
        assert config.provider == "openai"
        assert config.openai_api_key == "test123"
        assert config.config_file == str(current_env)

    def test_cli_args_override_env_provider(self):
        """CLI --provider flag should override .env DEFAULT_AI_PROVIDER."""
        # Given: .env with DEFAULT_AI_PROVIDER=anthropic
        # When: load_config(provider="openai")
        # Then: config.provider == "openai"
        pass

    def test_missing_required_api_key_raises_error(self):
        """Loading config for provider without API key should fail clearly."""
        # Given: .env with DEFAULT_AI_PROVIDER=anthropic but no ANTHROPIC_API_KEY
        # When: load_config()
        # Then: Raises ValueError with message about missing ANTHROPIC_API_KEY
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            load_config(provider="anthropic")
```

**Unit Test Coverage**: 40 tests minimum

#### Configuration Tests (10 tests)
```
✓ test_current_directory_env_takes_precedence
✓ test_git_repo_root_env_takes_precedence_over_home
✓ test_home_config_used_when_no_local_env
✓ test_cli_provider_overrides_env_provider
✓ test_cli_model_overrides_env_model
✓ test_missing_required_api_key_raises_error
✓ test_invalid_provider_raises_error
✓ test_timeout_seconds_parsed_as_int
✓ test_max_retries_parsed_as_int
✓ test_correlation_id_is_uuid
```

#### Git Parsing Tests (10 tests)
```
✓ test_get_commits_since_basic_range
✓ test_get_commits_with_empty_range
✓ test_get_commits_with_merge_commits
✓ test_commit_metadata_parsing
✓ test_diff_truncation_at_5000_chars
✓ test_get_recent_sync_point_from_reflog
✓ test_get_recent_sync_point_from_merge_commits
✓ test_get_recent_sync_point_fallback_to_head10
✓ test_get_commits_handles_invalid_ref
✓ test_get_commits_handles_no_git_repo
```

#### Retry Logic Tests (8 tests)
```
✓ test_retry_on_http_429_rate_limit
✓ test_retry_on_http_500_server_error
✓ test_exponential_backoff_timing
✓ test_max_retries_respected
✓ test_no_retry_on_http_401_auth_error
✓ test_no_retry_on_http_403_forbidden
✓ test_retry_on_connection_error
✓ test_retry_on_timeout
```

#### Prompt Generation Tests (12 tests)
```
✓ test_create_ai_prompt_basic_structure
✓ test_focus_mode_features
✓ test_focus_mode_security
✓ test_focus_mode_performance
✓ test_prompt_includes_commit_metadata
✓ test_prompt_includes_file_stats
✓ test_prompt_includes_relevant_diff
✓ test_prompt_filters_out_noise (test files, docs)
✓ test_prompt_truncates_long_diffs
✓ test_prompt_handles_empty_commits
✓ test_prompt_handles_binary_files
✓ test_prompt_handles_special_characters
```

---

### 2. Integration Tests

**Purpose**: Test component interactions and external integrations

**Scope**: Provider APIs, clipboard, installation

**Tools**:
- pytest
- vcrpy (record/replay HTTP interactions)
- docker (for installation testing)

**Test Structure**:
```python
# tests/integration/test_provider_anthropic.py
import pytest
import vcr
from git_ai_summary import AnthropicProvider, Config

@pytest.fixture
def anthropic_config():
    """Create test config for Anthropic provider."""
    return Config(
        provider="anthropic",
        anthropic_api_key="sk-ant-test-key",
        anthropic_model="claude-3-5-sonnet-latest",
        # ... other config fields
    )

@vcr.use_cassette('tests/fixtures/anthropic_success.yaml')
def test_anthropic_provider_successful_request(anthropic_config, logger):
    """Test successful API call with pre-recorded response."""
    provider = AnthropicProvider(anthropic_config, logger)

    system_prompt = "You are a helpful assistant."
    user_prompt = "Summarize these commits: ..."

    # Uses recorded response from fixture
    response = provider.generate(system_prompt, user_prompt)

    assert response is not None
    assert len(response) > 0
    assert "commit" in response.lower()

@vcr.use_cassette('tests/fixtures/anthropic_rate_limit.yaml')
def test_anthropic_provider_handles_rate_limit(anthropic_config, logger):
    """Test retry logic with rate limiting (429 response)."""
    provider = AnthropicProvider(anthropic_config, logger)

    # Recorded cassette contains 429 responses followed by success
    response = provider.generate("System prompt", "User prompt")

    # Should retry and eventually succeed
    assert response is not None

@vcr.use_cassette('tests/fixtures/anthropic_auth_error.yaml')
def test_anthropic_provider_auth_error(anthropic_config, logger):
    """Test authentication failure (401 response)."""
    provider = AnthropicProvider(anthropic_config, logger)

    # Recorded cassette contains 401 error
    with pytest.raises(ValueError, match="Authentication failed"):
        provider.generate("System prompt", "User prompt")
```

**Integration Test Coverage**: 18 tests minimum

#### Provider Tests (9 tests, one per provider)
```
✓ test_openai_provider_success
✓ test_anthropic_provider_success
✓ test_ollama_provider_success (mocked local server)
✓ test_openrouter_provider_success
✓ test_gemini_provider_success
✓ test_cohere_provider_success
✓ test_mistral_provider_success
✓ test_litellm_python_mode
✓ test_llm_cli_provider (mocked subprocess)
```

#### Installation Tests (3 tests)
```
✓ test_install_on_ubuntu_docker
✓ test_install_on_ubuntu_with_zsh
✓ test_install_rollback_on_failure
```

#### Clipboard Tests (3 tests)
```
✓ test_clipboard_pbcopy_macos
✓ test_clipboard_xclip_linux
✓ test_clipboard_fallback_when_unavailable
```

#### Health Check Tests (3 tests)
```
✓ test_health_check_success
✓ test_health_check_invalid_api_key
✓ test_health_check_connection_failure
```

---

### 3. Contract Tests

**Purpose**: Verify API request/response formats don't break

**Scope**: Provider API contracts

**Tools**:
- pytest
- pact (consumer-driven contracts)
- requests-mock (alternative to VCR)

**Test Structure**:
```python
# tests/contract/test_openai_contract.py
import pytest
from git_ai_summary import OpenAIProvider

def test_openai_request_format():
    """Verify we send correct request format to OpenAI API."""
    # Given: Expected OpenAI API request format
    expected_request = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "temperature": 0.2
    }

    # When: Provider makes API call
    # Then: Request matches expected format
    # (Use requests-mock to intercept and validate)
    pass

def test_openai_response_format():
    """Verify we can parse OpenAI API response format."""
    # Given: Sample OpenAI API response
    sample_response = {
        "choices": [
            {
                "message": {
                    "content": "Analysis of commits..."
                }
            }
        ]
    }

    # When: Provider parses response
    # Then: Extracts content correctly without errors
    pass
```

**Contract Test Coverage**: 9 tests (one per provider)

---

### 4. End-to-End Tests

**Purpose**: Test complete user workflows

**Scope**: Full CLI usage scenarios

**Tools**:
- pytest
- subprocess (CLI invocation)
- docker (clean environment)

**Test Structure**:
```python
# tests/e2e/test_cli_workflows.py
import subprocess
import pytest

def test_full_analysis_workflow(tmp_repo):
    """Test complete workflow: install → configure → analyze."""
    # Given: Clean git repo with commits
    # Given: Configured .env with valid API key

    # When: User runs analysis
    result = subprocess.run(
        ["./git-ai-summary.py", "--provider", "anthropic", "--since", "HEAD~5"],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Then: Analysis succeeds
    assert result.returncode == 0
    assert "=== Anthropic Analysis ===" in result.stdout
    assert len(result.stdout) > 100  # Non-empty analysis

def test_dry_run_workflow(tmp_repo):
    """Test dry-run workflow shows cost without API call."""
    # When: User runs dry-run
    result = subprocess.run(
        ["./git-ai-summary.py", "--dry-run", "--provider", "anthropic"],
        capture_output=True,
        text=True
    )

    # Then: Shows estimate without making API call
    assert "Estimated cost:" in result.stdout
    assert "[No API call made" in result.stdout
    assert result.returncode == 0

def test_health_check_workflow():
    """Test health check detects configuration issues."""
    # Given: Invalid API key
    # When: User runs health check
    # Then: Reports configuration problem with guidance
    pass
```

**E2E Test Coverage**: 5 tests minimum

---

## Test Infrastructure Setup

### Directory Structure

```
tests/
├── unit/
│   ├── __init__.py
│   ├── test_config_loading.py
│   ├── test_git_parsing.py
│   ├── test_retry_logic.py
│   └── test_prompt_generation.py
├── integration/
│   ├── __init__.py
│   ├── test_provider_openai.py
│   ├── test_provider_anthropic.py
│   ├── test_provider_ollama.py
│   ├── test_installation.py
│   ├── test_clipboard.py
│   └── test_health_check.py
├── contract/
│   ├── __init__.py
│   ├── test_openai_contract.py
│   ├── test_anthropic_contract.py
│   └── ...
├── e2e/
│   ├── __init__.py
│   └── test_cli_workflows.py
├── fixtures/
│   ├── sample_commits.json
│   ├── env_files/
│   │   ├── valid_anthropic.env
│   │   ├── missing_api_key.env
│   │   └── invalid_provider.env
│   └── vcr_cassettes/
│       ├── anthropic_success.yaml
│       ├── anthropic_rate_limit.yaml
│       ├── openai_success.yaml
│       └── ...
├── conftest.py  # Shared fixtures
└── README.md    # Test documentation
```

---

### pytest Configuration

**`pyproject.toml`** (or `pytest.ini`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

# Coverage settings
addopts = [
    "--cov=git_ai_summary",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=60",  # Fail if coverage < 60%
    "-v",  # Verbose output
    "--tb=short",  # Short traceback format
]

# Markers for test categorization
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (external dependencies)",
    "contract: Contract tests (API format validation)",
    "e2e: End-to-end tests (full workflows)",
    "slow: Slow tests (>5 seconds)",
]

# VCR.py configuration
vcr_record_mode = "once"  # Record cassettes once, replay thereafter
```

---

### Shared Fixtures (`conftest.py`)

```python
# tests/conftest.py
import pytest
import tempfile
import subprocess
from pathlib import Path
from git_ai_summary import Config
import logging

@pytest.fixture
def logger():
    """Provide test logger."""
    return logging.getLogger("test")

@pytest.fixture
def tmp_repo(tmp_path):
    """Create temporary git repository with sample commits."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir)

    # Create sample commits
    for i in range(5):
        file = repo_dir / f"file{i}.txt"
        file.write_text(f"Content {i}")
        subprocess.run(["git", "add", str(file)], cwd=repo_dir)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=repo_dir)

    return repo_dir

@pytest.fixture
def sample_config():
    """Provide sample valid configuration."""
    return Config(
        provider="anthropic",
        model=None,
        anthropic_api_key="sk-ant-test-key",
        anthropic_model="claude-3-5-sonnet-latest",
        # ... all required Config fields
    )

@pytest.fixture
def mock_env_file(tmp_path):
    """Create temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-test-123
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
    """.strip())
    return env_file
```

---

### VCR.py Setup for API Mocking

**Purpose**: Record real API responses once, replay in tests (no API calls)

**Installation**:
```bash
pip install vcrpy pytest-vcr
```

**Usage**:
```python
# tests/integration/test_provider_anthropic.py
import vcr

my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',  # Record on first run, replay thereafter
    match_on=['uri', 'method'],
    filter_headers=['authorization', 'x-api-key'],  # Don't record API keys
)

@my_vcr.use_cassette('anthropic_success.yaml')
def test_anthropic_success():
    # First run: Makes real API call, records to cassette
    # Subsequent runs: Replays from cassette, no API call
    provider = AnthropicProvider(config, logger)
    response = provider.generate("System", "User prompt")
    assert response is not None
```

**Recording Cassettes**:
```bash
# First run: Record real API responses (requires valid API keys)
ANTHROPIC_API_KEY=sk-ant-real-key pytest tests/integration/test_provider_anthropic.py

# Subsequent runs: Replay from cassettes (no API keys needed)
pytest tests/integration/test_provider_anthropic.py
```

---

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Category
```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Run tests with marker
pytest -m unit
pytest -m integration
pytest -m "not slow"  # Skip slow tests
```

### Run with Coverage Report
```bash
# Terminal report
pytest --cov=git_ai_summary --cov-report=term-missing

# HTML report (open htmlcov/index.html)
pytest --cov=git_ai_summary --cov-report=html

# Fail if coverage < 60%
pytest --cov-fail-under=60
```

### Run Specific Test
```bash
# Single test file
pytest tests/unit/test_config_loading.py

# Single test function
pytest tests/unit/test_config_loading.py::test_current_directory_env_takes_precedence

# Single test class
pytest tests/unit/test_config_loading.py::TestConfigLoading
```

### Debug Mode
```bash
# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show full diff for assertions
pytest -vv

# Drop into debugger on failure
pytest --pdb
```

---

## CI/CD Integration

### GitHub Actions Workflow

**`.github/workflows/test.yml`**:
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-vcr pytest-mock

      - name: Run tests with coverage
        run: |
          pytest --cov=git_ai_summary --cov-report=xml --cov-fail-under=60

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-${{ matrix.os }}-py${{ matrix.python-version }}
```

---

## Test Best Practices

### 1. Test Naming Convention

```python
# Good: Descriptive, tells what is being tested
def test_config_loading_prefers_current_directory_over_home():
    pass

# Bad: Vague, unclear intent
def test_config():
    pass
```

### 2. AAA Pattern (Arrange-Act-Assert)

```python
def test_retry_on_rate_limit():
    # Arrange: Set up test conditions
    config = Config(...)
    provider = OpenAIProvider(config, logger)

    # Act: Perform the action being tested
    with mock_response(status_code=429):
        response = provider.generate("System", "User")

    # Assert: Verify expected outcome
    assert response is not None
    assert retry_count == 3
```

### 3. Use Fixtures for Reusable Setup

```python
# Good: Reusable fixture
@pytest.fixture
def anthropic_provider(sample_config, logger):
    return AnthropicProvider(sample_config, logger)

def test_success(anthropic_provider):
    response = anthropic_provider.generate("System", "User")
    assert response is not None

# Bad: Repeated setup in each test
def test_success():
    config = Config(...)
    logger = logging.getLogger()
    provider = AnthropicProvider(config, logger)
    # ...
```

### 4. Test One Thing Per Test

```python
# Good: Focused test
def test_retry_count_increments():
    # Test only retry count behavior
    assert retry_count == expected_count

def test_retry_backoff_timing():
    # Test only backoff timing (separate test)
    assert wait_time == expected_time

# Bad: Testing multiple things
def test_retry_behavior():
    # Tests retry count AND backoff AND error handling
    assert retry_count == 3
    assert wait_time == 4
    assert error_message == "..."
```

### 5. Mock External Dependencies

```python
# Good: Mock external API call
@mock.patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value = mock_response(200, {"choices": [...]})
    response = provider.generate("System", "User")
    assert response is not None

# Bad: Make real API call in test
def test_api_call():
    # DON'T DO THIS: Uses real API, slow, costs money
    response = provider.generate("System", "User")
```

---

## Coverage Goals

### v1.1 Coverage Target: 60%

**Priority Coverage Areas**:
- ✅ Configuration loading (100% coverage)
- ✅ Retry logic (100% coverage)
- ✅ Git parsing (90% coverage)
- ✅ Prompt generation (80% coverage)
- ⚠️ Provider implementations (50% coverage via VCR)

### v1.2 Coverage Target: 80%

**Additional Coverage**:
- ✅ Provider implementations (80% coverage)
- ✅ Health check (100% coverage)
- ✅ Dry-run mode (100% coverage)
- ✅ Config validation (100% coverage)
- ✅ Installation script (70% coverage via Docker tests)

---

## Troubleshooting Test Issues

### Issue: VCR cassettes out of date

**Problem**: API format changed, cassettes contain old responses

**Solution**:
```bash
# Re-record cassettes with real API keys
rm tests/fixtures/vcr_cassettes/*.yaml
ANTHROPIC_API_KEY=sk-ant-real pytest tests/integration/
```

---

### Issue: Tests pass locally, fail in CI

**Problem**: Environment differences (OS, Python version, dependencies)

**Solution**:
- Check Python version matrix in CI (test 3.8, 3.9, 3.10, 3.11, 3.12)
- Pin dependency versions in requirements.txt
- Use Docker for consistent environment

---

### Issue: Flaky tests (sometimes pass, sometimes fail)

**Problem**: Tests depend on timing, random data, or external state

**Solution**:
- Mock time.sleep() in retry tests
- Use fixed random seeds: `random.seed(42)`
- Isolate tests from each other (use fresh fixtures)

---

## Appendix: Test Metrics

### Test Execution Time Targets

| Category | Time Target | Notes |
|----------|-------------|-------|
| Unit Tests | <5 seconds | Should be fast, no I/O |
| Integration Tests | <30 seconds | Uses VCR, minimal real API calls |
| Contract Tests | <10 seconds | Format validation only |
| E2E Tests | <60 seconds | Full workflows, slowest |
| **Total Suite** | **<2 minutes** | All tests combined |

---

### Test Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Update VCR cassettes | Quarterly | Engineering |
| Update provider pricing | Quarterly | Product |
| Review flaky tests | Monthly | QA |
| Update test dependencies | Monthly | Engineering |
| Coverage report review | Per PR | All contributors |

---

## References

- [REQUIREMENTS.md](REQUIREMENTS.md) - Test requirements (NFR-006)
- [PRD.md](PRD.md) - Testing roadmap (Sprint 3)
- [pytest documentation](https://docs.pytest.org/)
- [VCR.py documentation](https://vcrpy.readthedocs.io/)
