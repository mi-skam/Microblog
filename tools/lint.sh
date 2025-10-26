#!/bin/bash

# tools/lint.sh
# Lint the microblog project code and output results in JSON format

set -euo pipefail

# Script configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly INSTALL_SCRIPT="${PROJECT_ROOT}/tools/install.sh"

# Logging functions (only to stderr to keep stdout clean for JSON)
log_info() {
    echo "[INFO] $1" >&2
}

log_warn() {
    echo "[WARN] $1" >&2
}

log_error() {
    echo "[ERROR] $1" >&2
}

# Setup environment by running install script
setup_environment() {
    log_info "Setting up environment and dependencies..." >&2

    if [[ ! -f "${INSTALL_SCRIPT}" ]]; then
        log_error "Install script not found at ${INSTALL_SCRIPT}" >&2
        exit 1
    fi

    # Run install script silently and capture environment info
    if ! bash "${INSTALL_SCRIPT}" > /tmp/microblog_env.sh 2>/dev/null; then
        log_error "Failed to setup environment. Please check the install script." >&2
        exit 1
    fi

    # Source the environment
    # shellcheck source=/dev/null
    source /tmp/microblog_env.sh 2>/dev/null || true

    # Activate virtual environment if it exists
    if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${PROJECT_ROOT}/.venv/bin/activate" >&2 2>/dev/null
        log_info "Virtual environment activated" >&2
    fi
}

# Ensure pylint is installed
ensure_pylint_installed() {
    if ! command -v pylint &> /dev/null; then
        log_info "Installing pylint..." >&2
        pip install pylint &> /dev/null
    fi
    log_info "Pylint is available" >&2
}

# Convert pylint output to required JSON format
convert_pylint_to_json() {
    local pylint_output="$1"
    local json_output="["
    local first_entry=true

    # Process pylint output line by line
    while IFS= read -r line; do
        # Skip empty lines and lines that don't match the expected format
        if [[ -z "$line" || ! "$line" =~ ^[^:]+:[0-9]+:[0-9]*:.* ]]; then
            continue
        fi

        # Parse pylint output format: file:line:column: message-id message (symbol)
        if [[ "$line" =~ ^([^:]+):([0-9]+):([0-9]*):\ *([^:]+):\ *(.+)\ \(([^)]+)\)$ ]]; then
            local file="${BASH_REMATCH[1]}"
            local line_num="${BASH_REMATCH[2]}"
            local column="${BASH_REMATCH[3]:-0}"
            local msg_type="${BASH_REMATCH[4]}"
            local message="${BASH_REMATCH[5]}"
            local symbol="${BASH_REMATCH[6]}"

            # Only include syntax errors and critical warnings
            case "$msg_type" in
                "error"|"fatal"|"syntax-error")
                    local error_type="error"
                    ;;
                "warning")
                    # Only include critical warnings
                    case "$symbol" in
                        "undefined-variable"|"used-before-assignment"|"unreachable"|"duplicate-key")
                            local error_type="warning"
                            ;;
                        *)
                            continue
                            ;;
                    esac
                    ;;
                *)
                    continue
                    ;;
            esac

            # Add comma separator for subsequent entries
            if [[ "$first_entry" == false ]]; then
                json_output+=","
            fi
            first_entry=false

            # Build JSON object
            json_output+="{
  \"type\": \"$error_type\",
  \"path\": \"$file\",
  \"obj\": \"$symbol\",
  \"message\": \"$message\",
  \"line\": \"$line_num\",
  \"column\": \"$column\"
}"
        fi
    done <<< "$pylint_output"

    json_output+="]"
    echo "$json_output"
}

# Run pylint on the microblog package
run_pylint() {
    log_info "Running pylint on microblog package..." >&2

    local pylint_output
    local exit_code=0

    # Run pylint and capture output, allow it to fail
    set +e
    pylint_output=$(pylint "${PROJECT_ROOT}/microblog" \
        --output-format=text \
        --reports=no \
        --score=no \
        --disable=all \
        --enable=error,fatal,syntax-error,undefined-variable,used-before-assignment,unreachable,duplicate-key \
        2>/dev/null)
    local pylint_exit_code=$?
    set -e

    # Convert pylint output to JSON
    local json_result
    json_result=$(convert_pylint_to_json "$pylint_output")

    # Output JSON to stdout
    echo "$json_result"

    # Determine exit code based on whether any errors were found
    local error_count
    error_count=$(echo "$json_result" | grep -o '"type"' | wc -l || echo "0")

    if [[ "$error_count" -gt 0 ]]; then
        log_error "Found $error_count linting issues" >&2
        exit_code=1
    else
        log_info "No linting issues found" >&2
        exit_code=0
    fi

    return $exit_code
}

# Check if we're in a valid microblog project
validate_project() {
    if [[ ! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        log_error "Not in a microblog project directory (pyproject.toml not found)" >&2
        exit 1
    fi

    if [[ ! -d "${PROJECT_ROOT}/microblog" ]]; then
        log_error "microblog package directory not found" >&2
        exit 1
    fi

    log_info "Valid microblog project detected" >&2
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"

    log_info "Starting microblog linting..." >&2
    log_info "Project root: ${PROJECT_ROOT}" >&2

    validate_project
    setup_environment
    ensure_pylint_installed

    log_info "Environment ready, starting linting..." >&2
    run_pylint
}

# Run main function
main "$@"