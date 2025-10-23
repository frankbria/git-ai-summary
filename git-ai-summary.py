#!/usr/bin/env python3
# If running from venv, will use venv's python, otherwise system python3
"""
git-ai-summary.py - Summarize recent git changes using AI
"""

import subprocess
import sys
import json
import os
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional, Protocol
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


ProviderType = Literal["openai", "anthropic", "ollama", "openrouter", "gemini", "cohere", "mistral", "litellm", "llm"]


@dataclass
class Config:
    """Configuration for AI providers and global settings."""
    provider: ProviderType
    model: Optional[str]
    
    # API Keys
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    openrouter_api_key: Optional[str]
    google_api_key: Optional[str]
    cohere_api_key: Optional[str]
    mistral_api_key: Optional[str]
    litellm_api_key: Optional[str]
    
    # Base URLs
    openai_base_url: str
    anthropic_base_url: str
    openrouter_base_url: str
    gemini_base_url: str
    cohere_base_url: str
    mistral_base_url: str
    ollama_base_url: str
    litellm_base_url: str
    
    # Provider-specific models
    openai_model: str
    anthropic_model: str
    openrouter_model: str
    gemini_model: str
    cohere_model: str
    mistral_model: str
    ollama_model: str
    litellm_model: str
    llm_model: str
    
    # OpenRouter specific
    openrouter_site_url: str
    openrouter_app_name: str
    
    # LiteLLM specific
    litellm_mode: str
    
    # LLM CLI specific
    llm_extra_args: str
    
    # Global settings
    timeout: int
    max_retries: int
    log_level: str
    correlation_id: str
    config_file: Optional[str]  # Path to loaded .env file


class AIProvider(Protocol):
    """Protocol for AI provider implementations."""
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate AI response from prompts."""
        ...


def load_config(provider: Optional[str] = None, model: Optional[str] = None) -> Config:
    """Load configuration from environment and CLI arguments.
    
    Searches for .env file in the following order:
    1. Current directory (.env)
    2. Git repository root (.env)
    3. User config directory (~/.config/git-ai-summary/.env)
    4. Script's installation directory
    """
    # Try to find .env file in multiple locations
    env_locations = [
        Path.cwd() / ".env",  # Current directory
    ]
    
    # Try to find git repository root
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        if git_root.returncode == 0 and git_root.stdout.strip():
            git_root_path = Path(git_root.stdout.strip())
            if git_root_path != Path.cwd():
                env_locations.append(git_root_path / ".env")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # User config directory
    config_dir = Path.home() / ".config" / "git-ai-summary"
    env_locations.append(config_dir / ".env")
    
    # Script's directory (for installed version)
    script_dir = Path(__file__).parent
    env_locations.append(script_dir / ".env")
    
    # Load from the first .env file found
    env_file_loaded = None
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            env_file_loaded = env_path
            break
    
    # If no .env found, just load from environment
    if not env_file_loaded:
        load_dotenv()
    
    # Determine provider
    provider_str = provider or os.getenv("DEFAULT_AI_PROVIDER", "anthropic")
    valid_providers: tuple = ("openai", "anthropic", "ollama", "openrouter", "gemini", "cohere", "mistral", "litellm", "llm")
    
    if provider_str not in valid_providers:
        raise ValueError(
            f"Invalid provider '{provider_str}'. "
            f"Supported providers: {', '.join(valid_providers)}"
        )
    
    config = Config(
        provider=provider_str,  # type: ignore
        model=model,
        
        # API Keys
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        litellm_api_key=os.getenv("LITELLM_API_KEY"),
        
        # Base URLs
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1"),
        cohere_base_url=os.getenv("COHERE_BASE_URL", "https://api.cohere.com/v1"),
        mistral_base_url=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        litellm_base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
        
        # Models
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        cohere_model=os.getenv("COHERE_MODEL", "command-r-plus"),
        mistral_model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        litellm_model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        
        # OpenRouter specific
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "https://github.com/your/repo"),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "git-ai-summary"),
        
        # LiteLLM specific
        litellm_mode=os.getenv("LITELLM_MODE", "python"),
        
        # LLM CLI specific
        llm_extra_args=os.getenv("LLM_EXTRA_ARGS", ""),
        
        # Global settings
        timeout=int(os.getenv("AI_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("AI_MAX_RETRIES", "2")),
        log_level=os.getenv("AI_LOG_LEVEL", "INFO"),
        correlation_id=str(uuid.uuid4()),
        config_file=str(env_file_loaded) if env_file_loaded else None
    )
    
    # Validate required API keys
    validation_map = {
        "openai": (config.openai_api_key, "OPENAI_API_KEY"),
        "anthropic": (config.anthropic_api_key, "ANTHROPIC_API_KEY"),
        "openrouter": (config.openrouter_api_key, "OPENROUTER_API_KEY"),
        "gemini": (config.google_api_key, "GOOGLE_API_KEY"),
        "cohere": (config.cohere_api_key, "COHERE_API_KEY"),
        "mistral": (config.mistral_api_key, "MISTRAL_API_KEY"),
    }
    
    if config.provider in validation_map:
        key_value, key_name = validation_map[config.provider]
        if not key_value:
            raise ValueError(
                f"Provider '{config.provider}' requires {key_name} to be set. "
                f"Please add it to your .env file or set it as an environment variable."
            )
    
    return config


def get_commits_since(since_ref="HEAD~10", until_ref="HEAD"):
    """Get commits with their diffs."""
    
    # Get commit hashes
    result = subprocess.run(
        ["git", "rev-list", f"{since_ref}..{until_ref}"],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error getting commits: {result.stderr}")
        return []
    
    commit_hashes = result.stdout.strip().split('\n')
    if not commit_hashes or commit_hashes == ['']:
        return []
    
    commits = []
    for hash in commit_hashes:
        # Get commit info
        commit_info = subprocess.run(
            ["git", "show", "--format=%H|%an|%ae|%at|%s|%b", "--stat", hash],
            capture_output=True, text=True
        ).stdout
        
        # Get the actual diff
        diff = subprocess.run(
            ["git", "diff", f"{hash}^..{hash}"],
            capture_output=True, text=True
        ).stdout
        
        # Parse commit info
        lines = commit_info.split('\n')
        if lines:
            parts = lines[0].split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'timestamp': datetime.fromtimestamp(int(parts[3])).isoformat(),
                    'subject': parts[4],
                    'body': parts[5] if len(parts) > 5 else '',
                    'stats': '\n'.join(lines[2:]) if len(lines) > 2 else '',
                    'diff': diff[:5000] if len(diff) > 5000 else diff  # Truncate huge diffs
                })
    
    return commits

def get_recent_sync_point():
    """Try to detect when the last sync happened."""
    
    # Method 1: Check reflog for pull/merge operations
    result = subprocess.run(
        ["git", "reflog", "--grep-reflog=pull", "-n", "1", "--format=%H"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        return f"{result.stdout.strip()}^"
    
    # Method 2: Look for merge commits
    result = subprocess.run(
        ["git", "log", "--merges", "-n", "1", "--format=%H"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        return f"{result.stdout.strip()}^"
    
    # Default: last 10 commits
    return "HEAD~10"

def create_ai_prompt(commits, focus="features"):
    """Create a structured prompt for AI analysis."""
    
    prompt = f"""Analyze the following git commits and provide a summary focused on {focus}.

I'm particularly interested in:
1. New features or capabilities added
2. Changes to existing features
3. Breaking changes or important modifications
4. Anything that affects user-facing functionality

Please IGNORE:
- Bug fixes (unless they significantly change behavior)
- Refactoring or code organization changes
- Documentation updates
- Test additions
- Minor dependency updates

Format your response as:
## Key Features & Changes
- Brief description of each significant change

## Details (if needed)
- More context for complex changes

---
COMMITS TO ANALYZE:
"""
    
    for i, commit in enumerate(commits, 1):
        prompt += f"\n### Commit {i}: {commit['subject']}\n"
        prompt += f"Author: {commit['author']}\n"
        prompt += f"Date: {commit['timestamp']}\n"
        
        if commit['body']:
            prompt += f"Description: {commit['body']}\n"
        
        # Include file stats to show scope
        if commit['stats']:
            prompt += f"\nFiles changed:\n{commit['stats']}\n"
        
        # Include meaningful parts of the diff
        if commit['diff']:
            # Filter diff to focus on important files
            important_patterns = [
                r'\+\+\+ b/.*\.(py|js|ts|jsx|tsx|go|rs|java)$',  # Code files
                r'\+.*def |function |class |interface |struct ',  # New definitions
                r'\+.*export.*function|export.*class',  # Exported features
            ]
            
            lines = commit['diff'].split('\n')
            relevant_diff = []
            include_next = 0
            
            for line in lines:
                if line.startswith('+++') or line.startswith('---'):
                    relevant_diff.append(line)
                    include_next = 5  # Include next few lines for context
                elif include_next > 0:
                    relevant_diff.append(line)
                    include_next -= 1
                elif line.startswith('+') and not line.startswith('+++'):
                    # New additions that might be features
                    if 'TODO' not in line and 'console.log' not in line:
                        relevant_diff.append(line)
            
            if relevant_diff:
                prompt += f"\nKey diff sections:\n```diff\n"
                prompt += '\n'.join(relevant_diff[:50])  # Limit lines per commit
                prompt += "\n```\n"
        
        prompt += "\n---\n"
    
    return prompt


def _make_request_with_retry(url: str, headers: dict, data: dict, timeout: int, max_retries: int, logger: logging.Logger) -> requests.Response:
    """Make HTTP request with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            if response.status_code in (401, 403):
                raise ValueError(f"Authentication failed (HTTP {response.status_code}). Please check your API key.")
            
            if response.status_code == 429:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                raise ValueError("Rate limit exceeded. Please try again later.")
            
            if response.status_code >= 500:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error ({response.status_code}). Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Server error (HTTP {response.status_code}). Please try again later.")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                logger.warning(f"Request timeout. Retrying... (attempt {attempt + 1}/{max_retries + 1})")
                continue
            raise ValueError(f"Request timed out after {timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries:
                logger.warning(f"Connection error. Retrying... (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Connection failed: {str(e)}")
    
    raise ValueError("Max retries exceeded")


class OpenAIProvider:
    """OpenAI provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.openai_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        
        self.logger.info(f"Sending request to OpenAI (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"OpenAI response received in {duration:.2f}s")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class AnthropicProvider:
    """Anthropic (Claude) provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.anthropic_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.anthropic_base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.anthropic_api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 2048
        }
        
        self.logger.info(f"Sending request to Anthropic (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"Anthropic response received in {duration:.2f}s")
        
        result = response.json()
        return result["content"][0]["text"]


class OpenRouterProvider:
    """OpenRouter provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.openrouter_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.openrouter_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "HTTP-Referer": self.config.openrouter_site_url,
            "X-Title": self.config.openrouter_app_name,
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        self.logger.info(f"Sending request to OpenRouter (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"OpenRouter response received in {duration:.2f}s")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class GeminiProvider:
    """Google Gemini provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.gemini_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.gemini_base_url}/models/{self.model}:generateContent?key={self.config.google_api_key}"
        headers = {"Content-Type": "application/json"}
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": combined_prompt}]
                }
            ]
        }
        
        self.logger.info(f"Sending request to Gemini (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"Gemini response received in {duration:.2f}s")
        
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]


class CohereProvider:
    """Cohere provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.cohere_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.cohere_base_url}/chat"
        headers = {
            "Authorization": f"Bearer {self.config.cohere_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "message": user_prompt,
            "preamble": system_prompt
        }
        
        self.logger.info(f"Sending request to Cohere (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"Cohere response received in {duration:.2f}s")
        
        result = response.json()
        return result["text"]


class MistralProvider:
    """Mistral AI provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.mistral_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.mistral_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.mistral_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        self.logger.info(f"Sending request to Mistral (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"Mistral response received in {duration:.2f}s")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class OllamaProvider:
    """Ollama (local) provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.ollama_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.ollama_base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        data = {
            "model": self.model,
            "prompt": combined_prompt,
            "stream": False
        }
        
        self.logger.info(f"Sending request to Ollama (model: {self.model})")
        start_time = time.time()
        
        try:
            response = _make_request_with_retry(
                url, headers, data, self.config.timeout, self.config.max_retries, self.logger
            )
        except Exception as e:
            raise ValueError(
                f"Failed to connect to Ollama at {self.config.ollama_base_url}. "
                f"Make sure Ollama is running and the model '{self.model}' is installed. Error: {str(e)}"
            )
        
        duration = time.time() - start_time
        self.logger.info(f"Ollama response received in {duration:.2f}s")
        
        result = response.json()
        return result["response"]


class LiteLLMProvider:
    """LiteLLM provider implementation (supports multiple modes)."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.litellm_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        mode = self.config.litellm_mode.lower()
        
        if mode == "python":
            return self._generate_python(system_prompt, user_prompt)
        elif mode == "http":
            return self._generate_http(system_prompt, user_prompt)
        elif mode == "cli":
            return self._generate_cli(system_prompt, user_prompt)
        else:
            raise ValueError(f"Invalid LiteLLM mode: {mode}. Supported: python, http, cli")
    
    def _generate_python(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from litellm import completion
        except ImportError:
            raise ValueError("LiteLLM python mode requires 'litellm' package. Install: pip install litellm")
        
        self.logger.info(f"Sending request via LiteLLM Python (model: {self.model})")
        start_time = time.time()
        
        response = completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        duration = time.time() - start_time
        self.logger.info(f"LiteLLM Python response received in {duration:.2f}s")
        
        return response.choices[0].message.content
    
    def _generate_http(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.config.litellm_base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        if self.config.litellm_api_key:
            headers["Authorization"] = f"Bearer {self.config.litellm_api_key}"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        self.logger.info(f"Sending request via LiteLLM HTTP (model: {self.model})")
        start_time = time.time()
        
        response = _make_request_with_retry(
            url, headers, data, self.config.timeout, self.config.max_retries, self.logger
        )
        
        duration = time.time() - start_time
        self.logger.info(f"LiteLLM HTTP response received in {duration:.2f}s")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _generate_cli(self, system_prompt: str, user_prompt: str) -> str:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        self.logger.info(f"Sending request via LiteLLM CLI (model: {self.model})")
        start_time = time.time()
        
        result = subprocess.run(
            ["litellm", "--model", self.model, "--prompt", combined_prompt],
            capture_output=True,
            text=True,
            timeout=self.config.timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            raise ValueError(f"LiteLLM CLI failed: {result.stderr}")
        
        self.logger.info(f"LiteLLM CLI response received in {duration:.2f}s")
        return result.stdout.strip()


class LLMProvider:
    """LLM CLI (Simon Willison) provider implementation."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model = config.model or config.llm_model
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        cmd = ["llm", "-m", self.model]
        
        if self.config.llm_extra_args:
            cmd.extend(self.config.llm_extra_args.split())
        
        self.logger.info(f"Sending request via LLM CLI (model: {self.model})")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            input=combined_prompt,
            capture_output=True,
            text=True,
            timeout=self.config.timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            raise ValueError(f"LLM CLI failed: {result.stderr}")
        
        self.logger.info(f"LLM CLI response received in {duration:.2f}s")
        return result.stdout.strip()


def make_provider(config: Config, logger: logging.Logger) -> AIProvider:
    """Factory function to create appropriate AI provider."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "openrouter": OpenRouterProvider,
        "gemini": GeminiProvider,
        "cohere": CohereProvider,
        "mistral": MistralProvider,
        "ollama": OllamaProvider,
        "litellm": LiteLLMProvider,
        "llm": LLMProvider,
    }
    
    provider_class = providers.get(config.provider)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {config.provider}")
    
    return provider_class(config, logger)  # type: ignore


def send_to_ai(config: Config, system_prompt: str, user_prompt: str) -> str:
    """Send prompts to configured AI provider and get response."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"[{config.correlation_id}] Using provider: {config.provider}")
    logger.info(f"[{config.correlation_id}] Timeout: {config.timeout}s, Max retries: {config.max_retries}")
    
    provider = make_provider(config, logger)
    return provider.generate(system_prompt, user_prompt)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate AI-ready summary of recent commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported AI Providers:
  openai      - OpenAI GPT models
  anthropic   - Anthropic Claude models
  ollama      - Local Ollama models
  openrouter  - OpenRouter aggregator
  gemini      - Google Gemini models
  cohere      - Cohere models
  mistral     - Mistral AI models
  litellm     - LiteLLM (supports multiple modes)
  llm         - LLM CLI by Simon Willison

Configuration:
  Set up your .env file with API keys and provider settings.
  See .env.example for all available options.
        """
    )
    parser.add_argument('--since', default=None, help='Commit reference to start from (default: auto-detect)')
    parser.add_argument('--until', default='HEAD', help='Commit reference to end at (default: HEAD)')
    parser.add_argument('--output', '-o', help='Save analysis to file (when using AI provider)')
    parser.add_argument('--focus', default='features', help='Analysis focus (features/security/performance)')
    parser.add_argument('--copy', action='store_true', help='Copy prompt to clipboard for manual AI input (requires pbcopy/xclip)')
    parser.add_argument('--output-copy', action='store_true', help='Copy AI analysis to clipboard (requires pbcopy/xclip)')
    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic', 'ollama', 'openrouter', 'gemini', 'cohere', 'mistral', 'litellm', 'llm'],
        help='AI provider to use (overrides DEFAULT_AI_PROVIDER in .env)'
    )
    parser.add_argument('--model', help='Model to use (overrides provider-specific model in .env)')

    args = parser.parse_args()
    
    # Initialize logging
    try:
        config = load_config(provider=args.provider, model=args.model)
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper()),
            format=f'%(asctime)s - [{config.correlation_id[:8]}] - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        if config.config_file:
            logger.debug(f"Loaded configuration from: {config.config_file}")
        else:
            logger.debug("No .env file found, using environment variables only")
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Auto-detect sync point if not specified
    since_ref = args.since if args.since else get_recent_sync_point()
    
    print(f"Analyzing commits from {since_ref} to {args.until}...", file=sys.stderr)
    
    commits = get_commits_since(since_ref, args.until)
    
    if not commits:
        print("No commits found in the specified range.", file=sys.stderr)
        return
    
    print(f"Found {len(commits)} commits to analyze.", file=sys.stderr)
    
    user_prompt = create_ai_prompt(commits, args.focus)
    
    # Copy prompt to clipboard if requested (for manual AI input)
    if args.copy:
        try:
            subprocess.run(["pbcopy"], input=user_prompt, text=True, check=True)
            print("Prompt copied to clipboard!", file=sys.stderr)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["xclip", "-selection", "clipboard"], input=user_prompt, text=True, check=True)
                print("Prompt copied to clipboard!", file=sys.stderr)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Could not copy to clipboard (pbcopy/xclip not found)", file=sys.stderr)
    
    # If no provider is configured to send to AI, just output the prompt
    if not args.provider and not os.getenv("DEFAULT_AI_PROVIDER"):
        print(user_prompt)
        return
    
    # Send to AI provider
    try:
        print(f"Sending to {config.provider}...", file=sys.stderr)
        system_prompt = "You are a helpful AI assistant analyzing git commits."
        response = send_to_ai(config, system_prompt, user_prompt)
        
        # Display analysis (unless only saving to file)
        if not args.output:
            print(f"\n=== {config.provider.title()} Analysis ===\n")
            print(response)
        else:
            print(f"\n=== {config.provider.title()} Analysis ===\n", file=sys.stderr)
        
        # Save analysis to file
        if args.output:
            output_content = f"=== {config.provider.title()} Analysis ===\n\n{response}"
            Path(args.output).write_text(output_content)
            print(f"Analysis saved to {args.output}", file=sys.stderr)
        
        # Copy analysis to clipboard if requested
        if args.output_copy:
            try:
                subprocess.run(["pbcopy"], input=response, text=True, check=True)
                print("Analysis copied to clipboard!", file=sys.stderr)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=response, text=True, check=True)
                    print("Analysis copied to clipboard!", file=sys.stderr)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("Could not copy to clipboard (pbcopy/xclip not found)", file=sys.stderr)
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
