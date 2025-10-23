# Installation Guide

This guide explains how to install `git-ai-summary` for system-wide access from any directory.

## Quick Install

```bash
./install.sh
```

**New in v1.1**: Enhanced installation process with:
- ✅ **Pre-flight checks** - Validates Python 3.8+, Git, disk space, and permissions
- ✅ **Automatic shell detection** - Supports bash, zsh, and fish
- ✅ **Atomic installation** - Succeeds completely or rolls back on failure
- ✅ **Post-install validation** - Verifies installation actually works
- ✅ **Detailed logging** - Saves installation log to `/tmp/git-ai-summary-install-*.log`

The installer will:
1. Run pre-flight checks (Python, Git, disk space, permissions)
2. Create virtual environment in staging area
3. Install dependencies and validate
4. Create `~/bin/git-ai-summary` symlink
5. Set up `~/.config/git-ai-summary/` directory
6. Auto-detect your shell and update PATH configuration
7. Copy `.env.example` to `~/.config/git-ai-summary/.env`
8. Run post-install validation

## Configuration Priority

The tool searches for `.env` files in this order (first found wins):

1. **Current directory** (`.env`) - Per-project configuration
2. **Git repository root** (`.env`) - Repository-wide configuration
3. **User config** (`~/.config/git-ai-summary/.env`) - Global user settings
4. **Installation directory** (`.env`) - Fallback

This allows you to:
- Use global settings for most work
- Override with project-specific settings when needed
- Keep API keys in one secure location

## Setup Steps

### 1. Run Installation Script

```bash
cd /home/frankbria/projects/git-ai-summary
./install.sh
```

### 2. Add ~/bin to PATH (if needed)

If the installer warns that `~/bin` is not in your PATH, add this to `~/.bashrc`:

```bash
export PATH="$HOME/bin:$PATH"
```

Then reload:
```bash
source ~/.bashrc
```

### 3. Configure API Keys

Edit the global configuration:

```bash
nano ~/.config/git-ai-summary/.env
# or
code ~/.config/git-ai-summary/.env
```

Add your API key(s):
```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Test Installation

From any directory:
```bash
git-ai-summary --help
```

## Usage Examples

### From Any Directory

```bash
# Use global config
git-ai-summary --provider anthropic

# From any git repository
cd ~/projects/my-app
git-ai-summary --provider openai --since HEAD~10
```

### Per-Project Configuration

For project-specific settings, create `.env` in the project root:

```bash
cd ~/projects/my-special-project
cat > .env << 'EOF'
DEFAULT_AI_PROVIDER=openai
OPENAI_MODEL=gpt-4
EOF

# Now uses project-specific settings
git-ai-summary --provider openai
```

### Git Repository Configuration

For repository-wide settings (tracked in git or in `.gitignore`):

```bash
cd ~/projects/my-repo
git rev-parse --show-toplevel  # Find repo root

# Create .env at repo root
cat > .env << 'EOF'
DEFAULT_AI_PROVIDER=ollama
OLLAMA_MODEL=codellama
EOF

# Works from any subdirectory in the repo
cd src/components
git-ai-summary --provider ollama
```

## Configuration Scenarios

### Scenario 1: Single Global Config

Most users will want this:

```bash
# One-time setup
~/.config/git-ai-summary/.env:
  DEFAULT_AI_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-xxx

# Works everywhere
git-ai-summary --provider anthropic
```

### Scenario 2: Multiple Projects, Different Keys

```bash
# Global default
~/.config/git-ai-summary/.env:
  DEFAULT_AI_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-personal

# Work project override
~/work/project/.env:
  DEFAULT_AI_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-work
```

### Scenario 3: Testing Local AI

```bash
# Global: Use paid API
~/.config/git-ai-summary/.env:
  DEFAULT_AI_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-xxx

# Specific project: Use free local Ollama
~/experiments/project/.env:
  DEFAULT_AI_PROVIDER=ollama
  OLLAMA_MODEL=llama3.1:8b
```

## Troubleshooting

### Pre-flight Check Failures

#### Python not found or version too old

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# macOS
brew install python3

# Verify version (must be 3.8+)
python3 --version
```

#### Git not found

```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git
```

#### Insufficient disk space

The installer requires at least 100MB of free space. Check available space:

```bash
df -h $HOME
```

Free up space by removing unnecessary files or move the installation to a different location with more space.

#### Permission denied

If you see permission errors for `~/bin` or `~/.config`:

```bash
# Check ownership
ls -ld ~/bin ~/.config

# Should be owned by your user
# If not, fix permissions:
sudo chown -R $USER:$USER ~/bin ~/.config
```

### Installation Failures

If installation fails, check the installation log:

```bash
# Log location is shown in error message, typically:
cat /tmp/git-ai-summary-install-*.log

# Look for the most recent log
ls -lt /tmp/git-ai-summary-install-*.log | head -1
```

Common issues:
- **Dependency installation failed**: Check network connection, try again
- **Virtual environment creation failed**: Ensure `python3-venv` is installed
- **Validation failed**: Check that `git-ai-summary.py` is executable

### Command not found

**Check PATH:**
```bash
echo $PATH | grep "$HOME/bin"
```

If not found:
```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Check symlink:**
```bash
ls -la ~/bin/git-ai-summary
```

Should point to: `/home/frankbria/projects/git-ai-summary/git-ai-summary-wrapper.sh`

### Configuration not loading

**Debug which config is loaded:**
```bash
git-ai-summary --provider anthropic 2>&1 | grep "Loaded configuration"
```

**Check config file search order:**
```bash
# Current directory
ls -la .env

# Git repo root
git rev-parse --show-toplevel
ls -la $(git rev-parse --show-toplevel)/.env

# Global config
ls -la ~/.config/git-ai-summary/.env

# Installation directory
ls -la /home/frankbria/projects/git-ai-summary/.env
```

### Virtual environment not found

If you see import errors:

```bash
# Check venv exists
ls -la /home/frankbria/projects/git-ai-summary/venv/

# Recreate if needed
cd /home/frankbria/projects/git-ai-summary
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Uninstall

To remove the system-wide installation:

```bash
# Remove symlink
rm ~/bin/git-ai-summary

# Optionally remove global config
rm -rf ~/.config/git-ai-summary

# Keep the source installation intact for future use
```

## Advanced: System-wide Installation

For multiple users or system-wide access:

```bash
# Install to /usr/local/bin (requires sudo)
sudo ln -s /home/frankbria/projects/git-ai-summary/git-ai-summary-wrapper.sh /usr/local/bin/git-ai-summary

# Each user configures their own keys
# ~/.config/git-ai-summary/.env
```

## Alias Alternative

If you don't want to run the installer, add an alias to `~/.bashrc`:

```bash
alias git-ai-summary='/home/frankbria/projects/git-ai-summary/git-ai-summary-wrapper.sh'
```

Then:
```bash
source ~/.bashrc
git-ai-summary --help
```

## Development Mode

To work on the script while keeping it installed:

```bash
# Changes to the script are immediately available
cd /home/frankbria/projects/git-ai-summary
nano git-ai-summary.py

# Test from anywhere
cd /tmp
git-ai-summary --help  # Uses updated script
```

## Shell Completion (Optional)

For bash completion support, add to `~/.bashrc`:

```bash
# git-ai-summary completion
_git_ai_summary_completions() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    case "${prev}" in
        --provider)
            COMPREPLY=($(compgen -W "openai anthropic ollama openrouter gemini cohere mistral litellm llm" -- "${cur}"))
            return 0
            ;;
        --focus)
            COMPREPLY=($(compgen -W "features security performance" -- "${cur}"))
            return 0
            ;;
    esac
    
    COMPREPLY=($(compgen -W "--provider --model --since --until --output --focus --copy --output-copy --help" -- "${cur}"))
}

complete -F _git_ai_summary_completions git-ai-summary
```
