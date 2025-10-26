#!/bin/bash

# tools/run.sh
# Run the main microblog application

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

# Determine the appropriate run command based on project state and CLI availability
determine_run_command() {
    # Check if microblog CLI is available
    if command -v microblog &> /dev/null; then
        # Check if we should run serve or if there are specific arguments
        if [[ $# -eq 0 ]]; then
            log_info "Running microblog serve (default command)"
            microblog serve
        else
            log_info "Running microblog with provided arguments: $*"
            microblog "$@"
        fi
    else
        # Fallback to running the CLI module directly
        log_warn "microblog CLI not found, trying direct module execution"
        if [[ $# -eq 0 ]]; then
            log_info "Running python -m microblog.cli serve (fallback)"
            python -m microblog.cli serve
        else
            log_info "Running python -m microblog.cli with provided arguments: $*"
            python -m microblog.cli "$@"
        fi
    fi
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
Usage: $0 [COMMAND] [OPTIONS]

Run the microblog application with automatic environment setup.

Commands:
  serve          Start the development server (default)
  build          Build the static site
  status         Show project status
  create-user    Create a new admin user
  init           Initialize a new project
  --help         Show microblog CLI help

Options:
  All options are passed through to the microblog CLI.

Examples:
  $0                           # Start development server
  $0 serve --port 3000         # Start server on port 3000
  $0 build --output dist       # Build site to dist directory
  $0 status                    # Show project status
  $0 --help                    # Show full CLI help

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

    log_info "Starting microblog application..."
    log_info "Project root: ${PROJECT_ROOT}"

    validate_project
    setup_environment

    log_info "Environment ready, starting application..."
    determine_run_command "$@"
}

# Handle script interruption
trap 'log_warn "Application interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"