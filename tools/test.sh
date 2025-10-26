#!/bin/bash

# tools/test.sh
# Run the microblog project test suite

set -euo pipefail

# Color output for better readability
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly INSTALL_SCRIPT="${PROJECT_ROOT}/tools/install.sh"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Setup environment by running install script
setup_environment() {
    log_info "Setting up environment and dependencies..."

    if [[ ! -f "${INSTALL_SCRIPT}" ]]; then
        log_error "Install script not found at ${INSTALL_SCRIPT}"
        exit 1
    fi

    # Run install script and capture environment info
    if ! bash "${INSTALL_SCRIPT}" > /tmp/microblog_env.sh 2>/dev/null; then
        log_error "Failed to setup environment. Please check the install script."
        exit 1
    fi

    # Source the environment
    # shellcheck source=/dev/null
    source /tmp/microblog_env.sh 2>/dev/null || true

    # Activate virtual environment if it exists
    if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${PROJECT_ROOT}/.venv/bin/activate"
        log_info "Virtual environment activated"
    fi
}

# Ensure pytest is available
ensure_pytest_installed() {
    if ! command -v pytest &> /dev/null; then
        log_warn "pytest not found, checking if it's available via Python module..."
        if ! python -m pytest --version &> /dev/null; then
            log_error "pytest is not installed. Installing pytest..."
            pip install pytest pytest-asyncio pytest-cov httpx
        fi
    fi
    log_info "pytest is available"
}

# Run the test suite
run_tests() {
    log_info "Running test suite..."

    local test_args=()
    local exit_code=0

    # Check if tests directory exists
    if [[ ! -d "${PROJECT_ROOT}/tests" ]]; then
        log_warn "Tests directory not found at ${PROJECT_ROOT}/tests"
        log_info "Creating basic test structure..."
        mkdir -p "${PROJECT_ROOT}/tests"

        # Create a basic test file if none exists
        if [[ ! -f "${PROJECT_ROOT}/tests/test_basic.py" ]]; then
            cat > "${PROJECT_ROOT}/tests/test_basic.py" << 'EOF'
"""
Basic tests for microblog package structure.
"""

import pytest
from pathlib import Path


def test_package_imports():
    """Test that the main package can be imported."""
    import microblog
    assert microblog is not None


def test_cli_imports():
    """Test that the CLI module can be imported."""
    from microblog import cli
    assert cli is not None


def test_utils_imports():
    """Test that the utils module can be imported."""
    from microblog import utils
    assert utils is not None


def test_project_structure():
    """Test that key project files exist."""
    project_root = Path(__file__).parent.parent

    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "microblog").is_dir()
    assert (project_root / "microblog" / "__init__.py").exists()
    assert (project_root / "microblog" / "cli.py").exists()
EOF
            log_info "Created basic test file at tests/test_basic.py"
        fi
    fi

    # Determine pytest arguments
    if [[ $# -eq 0 ]]; then
        # Default test configuration from pyproject.toml
        test_args=(
            "${PROJECT_ROOT}/tests"
            "--cov=microblog"
            "--cov-report=term-missing"
            "-v"
        )
    else
        # Pass through user arguments
        test_args=("$@")
    fi

    log_info "Running pytest with arguments: ${test_args[*]}"

    # Run pytest
    if python -m pytest "${test_args[@]}"; then
        log_info "All tests passed successfully!"
        exit_code=0
    else
        log_error "Some tests failed!"
        exit_code=1
    fi

    return $exit_code
}

# Check if we're in a valid microblog project
validate_project() {
    if [[ ! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        log_error "Not in a microblog project directory (pyproject.toml not found)"
        exit 1
    fi

    # Check if this is actually a microblog project
    if ! grep -q "name = \"microblog\"" "${PROJECT_ROOT}/pyproject.toml" 2>/dev/null; then
        log_error "This doesn't appear to be a microblog project"
        exit 1
    fi

    log_info "Valid microblog project detected"
}

# Display usage information
show_usage() {
    cat << EOF
Usage: $0 [PYTEST_OPTIONS]

Run the microblog project test suite with automatic environment setup.

Examples:
  $0                           # Run all tests with default options
  $0 -k "test_cli"            # Run only tests matching pattern
  $0 tests/unit/              # Run tests in specific directory
  $0 --no-cov                 # Run tests without coverage
  $0 -v --tb=short            # Run with verbose output and short traceback

All arguments are passed directly to pytest.

EOF
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"

    # Show help if requested
    if [[ $# -eq 1 && ("$1" == "-h" || "$1" == "--help" || "$1" == "help") ]]; then
        show_usage
        exit 0
    fi

    log_info "Starting microblog test suite..."
    log_info "Project root: ${PROJECT_ROOT}"

    validate_project
    setup_environment
    ensure_pytest_installed

    log_info "Environment ready, starting tests..."
    run_tests "$@"
}

# Handle script interruption
trap 'log_warn "Test run interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"