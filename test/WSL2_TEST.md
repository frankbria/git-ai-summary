# WSL2 Ubuntu Manual Testing Guide

## Prerequisites

- Windows 10/11 with WSL2 enabled
- Ubuntu 20.04 or 22.04 installed in WSL2
- Access to terminal

## Test Procedure

### 1. Verify WSL2 Environment

```bash
# Check WSL version (run in PowerShell on Windows)
wsl --list --verbose

# Expected: Ubuntu distribution running version 2

# Launch Ubuntu terminal
wsl -d Ubuntu
```

### 2. Fresh Installation Test

```bash
# Update package lists (in WSL Ubuntu)
sudo apt update

# Install prerequisites if needed
sudo apt install python3 python3-pip python3-venv git -y

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
# - PATH added to ~/.bashrc
```

### 3. Verify Installation

```bash
# Source shell config
source ~/.bashrc

# Test help command
git-ai-summary --help

# Expected: Help text displays without errors
```

### 4. Test from Different Directory

```bash
cd /tmp
git-ai-summary --help

# Expected: Command works from any directory
```

### 5. Test with WSL-Specific Scenarios

#### Test with Windows-mounted drives

```bash
cd /mnt/c/Users/YourUsername/
git-ai-summary --help

# Expected: Works correctly even on Windows filesystem
```

#### Test with symbolic links

```bash
# Create test git repo on Windows filesystem
cd /mnt/c/temp
git init test-repo
cd test-repo
echo "test" > file.txt
git add . && git commit -m "test"

# Run git-ai-summary
git-ai-summary --provider anthropic --since HEAD~1 --copy

# Expected: Handles Windows filesystem correctly
```

### 6. Test Re-installation

```bash
# Re-run installer
cd ~/git-ai-summary
./install.sh

# Expected:
# - Detects existing installation
# - Successfully re-installs
```

## WSL2-Specific Considerations

### Issue: PATH not persistent across restarts

**Solution**: Ensure ~/.bashrc modification is correct

```bash
# Check ~/.bashrc for PATH entry
grep "HOME/bin" ~/.bashrc

# Should show: export PATH="$HOME/bin:$PATH"
```

### Issue: Python not found

**Solution**: Install Python in WSL (not Windows)

```bash
sudo apt install python3 python3-pip python3-venv
```

### Issue: Git not configured

**Solution**: Configure git in WSL

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Performance Notes

- Installation on WSL2 may be slightly slower than native Linux
- Windows Defender may scan venv creation (causes delays)
- First run may take longer due to Windows filesystem overhead

## Success Criteria

- ✅ Installation completes without errors
- ✅ `git-ai-summary --help` works from any directory
- ✅ Works on both Linux filesystem (/home) and Windows mounts (/mnt/c)
- ✅ PATH persists across terminal sessions
- ✅ Re-installation works correctly

## Report Results

If all tests pass, create GitHub issue with:
- Title: "WSL2 Ubuntu testing passed"
- WSL2 version (from `wsl --version` in PowerShell)
- Ubuntu version (from `lsb_release -a`)
- Python version (from `python3 --version`)

If any tests fail, create GitHub issue with:
- Title: "WSL2 Ubuntu installation failure"
- Full error output
- Installation log: `/tmp/git-ai-summary-install-XXXXX.log`
- WSL and Ubuntu version info
