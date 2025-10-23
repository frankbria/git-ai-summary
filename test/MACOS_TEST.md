# macOS Manual Testing Guide

## Prerequisites

- macOS 10.15+ (Catalina or later)
- Homebrew installed (optional, for installing dependencies)
- Terminal.app or iTerm2

## Test Procedure

### 1. Fresh Installation Test

```bash
# Clone repository
git clone https://github.com/yourusername/git-ai-summary.git
cd git-ai-summary

# Run installation
./install.sh

# Expected output:
# - Pre-flight checks pass
# - Virtual environment created
# - Dependencies installed
# - Symlink created
# - PATH added to ~/.zshrc (default on macOS Catalina+)
```

### 2. Verify Installation

```bash
# Source shell config (zsh is default on modern macOS)
source ~/.zshrc

# Test help command
git-ai-summary --help

# Expected: Help text displays without errors
```

### 3. Test from Different Directory

```bash
cd /tmp
git-ai-summary --help

# Expected: Command works from any directory
```

### 4. Test with Different Shells

#### Bash (if available)

```bash
# Switch to bash
bash

# Source config
source ~/.bash_profile

# Test
git-ai-summary --help
```

### 5. Test Re-installation

```bash
# Re-run installer
cd ~/path/to/git-ai-summary
./install.sh

# Expected:
# - Detects existing installation
# - Offers to replace
# - Successfully re-installs
```

## Common Issues

### Issue: "command not found: git-ai-summary"

**Solution**: PATH not updated

```bash
# Check if ~/bin is in PATH
echo $PATH | grep "$HOME/bin"

# If not, source your shell config
source ~/.zshrc  # or ~/.bash_profile for bash
```

### Issue: "Permission denied"

**Solution**: Check symlink permissions

```bash
ls -la ~/bin/git-ai-summary

# Should show symlink pointing to installation directory
```

### Issue: Python version too old

**Solution**: Install Python 3.8+ via Homebrew

```bash
brew install python@3.11
```

## Success Criteria

- ✅ Installation completes without errors
- ✅ `git-ai-summary --help` works from any directory
- ✅ PATH automatically updated in ~/.zshrc
- ✅ Re-installation works correctly
- ✅ No permission errors

## Report Results

If all tests pass, create GitHub issue with:
- Title: "macOS testing passed on [macOS version]"
- macOS version (from `sw_vers`)
- Python version (from `python3 --version`)
- Shell type (zsh/bash)

If any tests fail, create GitHub issue with:
- Title: "macOS installation failure on [macOS version]"
- Full error output
- Installation log: `/tmp/git-ai-summary-install-XXXXX.log`
