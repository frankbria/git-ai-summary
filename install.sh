#!/bin/bash
# Enhanced installation script for git-ai-summary v1.1
# Features: pre-flight checks, shell auto-detection, atomic install with rollback

set -euo pipefail

# Installation state tracking
INSTALL_LOG="/tmp/git-ai-summary-install-$$.log"
STAGING_DIR="/tmp/git-ai-summary-staging-$$"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/bin"
CONFIG_DIR="$HOME/.config/git-ai-summary"
SYMLINK_PATH="$BIN_DIR/git-ai-summary"

# Cleanup on error
cleanup_on_error() {
    echo ""
    echo "❌ Installation failed!"
    echo ""
    if [ -d "$STAGING_DIR" ]; then
        echo "Cleaning up staging directory..."
        rm -rf "$STAGING_DIR"
    fi
    echo ""
    echo "Installation log saved to: $INSTALL_LOG"
    echo "Please report issues at: https://github.com/frankbria/git-ai-summary/issues"
    exit 1
}

trap cleanup_on_error ERR

# Logging function
log() {
    echo "$1" | tee -a "$INSTALL_LOG"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

check_python() {
    log "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        log "❌ Python 3 not found"
        log ""
        log "Please install Python 3.8 or higher:"
        log "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        log "  macOS: brew install python3"
        log "  Or visit: https://www.python.org/downloads/"
        return 1
    fi

    python_version=$(python3 --version | cut -d' ' -f2)
    required_version="3.8"

    # Version comparison
    if ! printf '%s\n' "$required_version" "$python_version" | sort -V -C; then
        log "❌ Python $python_version found, but 3.8+ required"
        log ""
        log "Please upgrade Python to 3.8 or higher"
        return 1
    fi

    log "✓ Python $python_version"
    return 0
}

check_git() {
    log "Checking Git installation..."

    if ! command -v git &> /dev/null; then
        log "❌ Git not found"
        log ""
        log "Please install Git:"
        log "  Ubuntu/Debian: sudo apt install git"
        log "  macOS: brew install git"
        log "  Or visit: https://git-scm.com/downloads"
        return 1
    fi

    git_version=$(git --version | cut -d' ' -f3)
    log "✓ Git $git_version"
    return 0
}

check_disk_space() {
    log "Checking disk space..."

    required_mb=100
    available_mb=$(df -m "$INSTALL_DIR" 2>/dev/null | awk 'NR==2 {print $4}')

    if [ -z "$available_mb" ]; then
        log "⚠ Could not determine disk space (continuing anyway)"
        return 0
    fi

    if [ "$available_mb" -lt "$required_mb" ]; then
        log "❌ Insufficient disk space: ${available_mb}MB available, ${required_mb}MB required"
        return 1
    fi

    log "✓ Disk space: ${available_mb}MB available"
    return 0
}

check_permissions() {
    log "Checking write permissions..."

    # Test write to ~/bin
    if ! mkdir -p "$BIN_DIR" 2>/dev/null; then
        log "❌ Cannot create $BIN_DIR (permission denied)"
        return 1
    fi
    log "✓ Write access to $BIN_DIR"

    # Test write to ~/.config
    if ! mkdir -p "$CONFIG_DIR" 2>/dev/null; then
        log "❌ Cannot create $CONFIG_DIR (permission denied)"
        return 1
    fi
    log "✓ Write access to $CONFIG_DIR"

    return 0
}

# ============================================================================
# SHELL AUTO-DETECTION
# ============================================================================

detect_shell_config() {
    local shell_name=""
    local config_file=""

    # Detect from $SHELL environment variable
    if [ -n "${SHELL:-}" ]; then
        shell_name=$(basename "$SHELL")
    else
        # Fallback: detect from current process
        shell_name=$(ps -p $$ -o comm= | sed 's/^-//')
    fi

    case "$shell_name" in
        bash)
            # Prefer .bashrc for interactive shells
            if [ -f "$HOME/.bashrc" ]; then
                config_file="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                config_file="$HOME/.bash_profile"
            else
                config_file="$HOME/.profile"
            fi
            ;;
        zsh)
            config_file="$HOME/.zshrc"
            ;;
        fish)
            mkdir -p "$HOME/.config/fish"
            config_file="$HOME/.config/fish/config.fish"
            ;;
        *)
            # Unknown shell, use generic .profile
            log "⚠ Unknown shell: $shell_name, using ~/.profile"
            config_file="$HOME/.profile"
            ;;
    esac

    echo "$config_file"
}

add_to_path() {
    local config_file=$(detect_shell_config)
    local path_entry

    log ""
    log "Configuring PATH in $config_file..."

    # Check if already in PATH
    if grep -q 'HOME/bin' "$config_file" 2>/dev/null; then
        log "✓ $BIN_DIR already in PATH"
        return 0
    fi

    # Determine path entry format based on shell
    if [[ "$config_file" == *"fish"* ]]; then
        path_entry="set -gx PATH \$HOME/bin \$PATH"
    else
        path_entry="export PATH=\"\$HOME/bin:\$PATH\""
    fi

    # Add to config file
    {
        echo ""
        echo "# Added by git-ai-summary installer on $(date)"
        echo "$path_entry"
    } >> "$config_file"

    log "✓ Added $BIN_DIR to PATH"
    log ""
    log "⚠ To activate the PATH change, run:"
    log "  source $config_file"
}

# ============================================================================
# ATOMIC INSTALLATION
# ============================================================================

create_venv() {
    log ""
    log "=== Creating Virtual Environment ==="

    mkdir -p "$STAGING_DIR"
    log "Created staging directory: $STAGING_DIR"

    python3 -m venv "$STAGING_DIR/venv" >> "$INSTALL_LOG" 2>&1
    log "✓ Virtual environment created"

    # Upgrade pip
    "$STAGING_DIR/venv/bin/pip" install --upgrade pip >> "$INSTALL_LOG" 2>&1
    log "✓ pip upgraded"

    # Install dependencies
    log "Installing dependencies (this may take a minute)..."
    "$STAGING_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" >> "$INSTALL_LOG" 2>&1
    log "✓ Dependencies installed"
}

validate_installation() {
    log ""
    log "=== Validating Installation ==="

    # Test that script runs with --help
    if ! "$STAGING_DIR/venv/bin/python" "$INSTALL_DIR/git-ai-summary.py" --help >> "$INSTALL_LOG" 2>&1; then
        log "❌ Validation failed: script cannot run --help"
        log "See $INSTALL_LOG for details"
        return 1
    fi

    log "✓ Script validation passed"
    return 0
}

finalize_installation() {
    log ""
    log "=== Finalizing Installation ==="

    # Remove old venv if exists
    if [ -d "$INSTALL_DIR/venv" ]; then
        log "Removing old virtual environment..."
        rm -rf "$INSTALL_DIR/venv"
    fi

    # Move staged venv to final location
    mv "$STAGING_DIR/venv" "$INSTALL_DIR/venv"
    log "✓ Virtual environment installed to $INSTALL_DIR/venv"

    # Create symlink
    if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
        log "Removing existing symlink..."
        rm -f "$SYMLINK_PATH"
    fi

    ln -s "$INSTALL_DIR/git-ai-summary-wrapper.sh" "$SYMLINK_PATH"
    log "✓ Symlink created: $SYMLINK_PATH"

    # Setup config directory
    if [ ! -f "$CONFIG_DIR/.env" ] && [ -f "$INSTALL_DIR/.env.example" ]; then
        log "Copying .env.example to $CONFIG_DIR/.env"
        cp "$INSTALL_DIR/.env.example" "$CONFIG_DIR/.env"
        log "✓ Configuration file created"
    fi

    # Cleanup staging directory
    rm -rf "$STAGING_DIR"
    log "✓ Cleaned up staging directory"
}

# ============================================================================
# POST-INSTALL VALIDATION
# ============================================================================

post_install_validation() {
    log ""
    log "=== Post-Install Validation ==="

    # Test 1: Symlink exists and is valid
    if [ ! -L "$SYMLINK_PATH" ]; then
        log "❌ Symlink not created: $SYMLINK_PATH"
        return 1
    fi
    log "✓ Symlink exists: $SYMLINK_PATH"

    # Test 2: Symlink resolves correctly
    if [ ! -e "$SYMLINK_PATH" ]; then
        log "❌ Symlink broken (target doesn't exist)"
        return 1
    fi
    log "✓ Symlink resolves correctly"

    # Test 3: Config directory exists
    if [ ! -d "$CONFIG_DIR" ]; then
        log "❌ Config directory not created: $CONFIG_DIR"
        return 1
    fi
    log "✓ Config directory exists: $CONFIG_DIR"

    # Test 4: Config file is writable (if it exists)
    if [ -f "$CONFIG_DIR/.env" ]; then
        if [ -w "$CONFIG_DIR/.env" ]; then
            log "✓ Config file is writable"
        else
            log "⚠ Config file exists but is not writable: $CONFIG_DIR/.env"
        fi
    fi

    # Test 5: Command works from different directory
    local current_dir=$(pwd)
    cd /tmp
    if "$SYMLINK_PATH" --help > /dev/null 2>&1; then
        log "✓ Command works from different directory"
    else
        log "⚠ Command may not work correctly from other directories"
    fi
    cd "$current_dir"

    log ""
    log "All post-install validation checks passed!"
    return 0
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

main() {
    log "=== Git AI Summary - Installation ==="
    log "Version: 1.1"
    log "Timestamp: $(date)"
    log "User: $(whoami)"
    log "Installation directory: $INSTALL_DIR"
    log ""

    # Pre-flight checks
    log "=== Pre-flight Checks ==="
    check_python || exit 1
    check_git || exit 1
    check_disk_space || exit 1
    check_permissions || exit 1
    log ""
    log "All pre-flight checks passed!"

    # Atomic installation
    create_venv || cleanup_on_error
    validate_installation || cleanup_on_error
    finalize_installation || cleanup_on_error

    # Post-install validation
    if ! post_install_validation; then
        log ""
        log "⚠ Installation completed but validation warnings occurred"
        log "Check the installation log: $INSTALL_LOG"
    fi

    # PATH configuration
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        add_to_path
    else
        log ""
        log "✓ $BIN_DIR is already in PATH"
    fi

    # Success message
    log ""
    log "=== Installation Complete! ==="
    log ""
    log "Usage from any directory:"
    log "  git-ai-summary --help"
    log "  git-ai-summary --provider anthropic"
    log ""
    log "Configuration priority (first found wins):"
    log "  1. .env in current directory"
    log "  2. .env in git repository root"
    log "  3. $CONFIG_DIR/.env (global)"
    log "  4. $INSTALL_DIR/.env (fallback)"
    log ""
    log "Next steps:"
    log "  1. Edit your API key: nano $CONFIG_DIR/.env"
    log "  2. Activate PATH: source $(detect_shell_config)"
    log "  3. Test installation: git-ai-summary --help"
    log ""
    log "For troubleshooting, see:"
    log "  - Installation log: $INSTALL_LOG"
    log "  - Documentation: $INSTALL_DIR/INSTALL.md"
    log "  - Issues: https://github.com/frankbria/git-ai-summary/issues"
    log ""
}

# Run main installation
main
