#!/bin/bash
# Automated installation testing on multiple platforms

set -e

echo "=== Git AI Summary - Installation Tests ==="
echo ""
echo "Testing installation on clean Docker environments"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name=$1
    local dockerfile=$2

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if docker build -f "$dockerfile" -t "git-ai-summary-test-$test_name" . ; then
        echo -e "${GREEN}✓ $test_name: PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $test_name: FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
    echo ""
}

# Test 1: Ubuntu with bash
run_test "ubuntu-bash" "test/Dockerfile.ubuntu-bash"

# Test 2: Ubuntu with zsh
run_test "ubuntu-zsh" "test/Dockerfile.ubuntu-zsh"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All automated tests passed!${NC}"
    echo ""
    echo "Manual testing required for:"
    echo "  - macOS (see test/MACOS_TEST.md)"
    echo "  - WSL2 Ubuntu (see test/WSL2_TEST.md)"
    exit 0
else
    echo -e "${RED}Some tests failed. Check output above for details.${NC}"
    exit 1
fi
