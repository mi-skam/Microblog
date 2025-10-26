#!/bin/bash

# tools/install.sh
# Environment setup and dependency installation for microblog project

set -euo pipefail

# Color output for better readability
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly VENV_DIR="${PROJECT_ROOT}/.venv"
readonly PYTHON_VERSION="3.10"

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

# Check if Python is available and meets minimum version
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi

    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        log_error "Python ${PYTHON_VERSION}+ is required, but found Python ${python_version}"
        exit 1
    fi

    log_info "Python ${python_version} detected"
}

# Create virtual environment if it doesn't exist
setup_virtual_environment() {
    if [[ ! -d "${VENV_DIR}" ]]; then
        log_info "Creating virtual environment at ${VENV_DIR}"
        python3 -m venv "${VENV_DIR}"
    else
        log_info "Virtual environment already exists at ${VENV_DIR}"
    fi

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
    log_info "Virtual environment activated"

    # Upgrade pip to latest version
    log_info "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
}

# Install dependencies from requirements.txt and pyproject.toml
install_dependencies() {
    log_info "Installing project dependencies..."

    # Install from requirements.txt if it exists
    if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
        log_info "Installing dependencies from requirements.txt"
        pip install -r "${PROJECT_ROOT}/requirements.txt" --quiet
    fi

    # Install project in editable mode with development dependencies
    if [[ -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        log_info "Installing project in editable mode with development dependencies"
        pip install -e "${PROJECT_ROOT}[dev]" --quiet
    else
        log_warn "pyproject.toml not found, skipping editable install"
    fi

    log_info "Dependencies installed successfully"
}

# Verify installation by checking key dependencies
verify_installation() {
    log_info "Verifying installation..."

    # Check if microblog CLI is available
    if command -v microblog &> /dev/null; then
        log_info "microblog CLI is available"
        # Test CLI help command
        if microblog --help &> /dev/null; then
            log_info "microblog CLI is working correctly"
        else
            log_warn "microblog CLI installed but --help command failed"
        fi
    else
        log_warn "microblog CLI not found in PATH after installation"
    fi

    # Check critical dependencies
    local dependencies=("fastapi" "click" "uvicorn" "jinja2" "markdown")
    for dep in "${dependencies[@]}"; do
        if python -c "import ${dep}" 2>/dev/null; then
            log_info "✓ ${dep} is available"
        else
            log_error "✗ ${dep} is not available"
            exit 1
        fi
    done

    log_info "Installation verification completed successfully"
}

# Print environment information for other scripts
print_environment_info() {
    echo "# Environment information for sourcing by other scripts"
    echo "export VIRTUAL_ENV='${VENV_DIR}'"
    echo "export PATH='${VENV_DIR}/bin:\$PATH'"
    echo "export PYTHONPATH='${PROJECT_ROOT}:\$PYTHONPATH'"
    echo "# To activate this environment, run: source ${VENV_DIR}/bin/activate"
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"

    log_info "Starting microblog environment setup..."
    log_info "Project root: ${PROJECT_ROOT}"

    check_python
    setup_virtual_environment
    install_dependencies
    verify_installation

    log_info "Environment setup completed successfully!"
    log_info ""
    log_info "To activate the environment manually, run:"
    log_info "  source ${VENV_DIR}/bin/activate"
    log_info ""
    log_info "To test the installation, run:"
    log_info "  microblog --help"

    # Print environment info for other scripts to source
    print_environment_info
}

# Run main function
main "$@"