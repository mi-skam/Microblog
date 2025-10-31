#!/bin/bash
# Production deployment script for MicroBlog
# Usage: ./scripts/deploy.sh [--backup] [--no-build] [--config CONFIG_PATH]

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_NAME="microblog"
APP_USER="microblog"
APP_DIR="/opt/microblog"
BACKUP_DIR="$APP_DIR/backups"
SYSTEMD_SERVICE="microblog.service"

# Default options
DO_BACKUP=true
DO_BUILD=true
CONFIG_PATH=""
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            DO_BACKUP=true
            shift
            ;;
        --no-backup)
            DO_BACKUP=false
            shift
            ;;
        --no-build)
            DO_BUILD=false
            shift
            ;;
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Deploy MicroBlog to production"
            echo ""
            echo "Options:"
            echo "  --backup         Create backup before deployment (default)"
            echo "  --no-backup      Skip backup creation"
            echo "  --no-build       Skip building static site"
            echo "  --config PATH    Use specific configuration file"
            echo "  --verbose, -v    Enable verbose output"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if running as root (required for systemd operations)
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root for systemd operations"
    log_info "Please run: sudo $0"
    exit 1
fi

# Verify required directories exist
if [[ ! -d "$APP_DIR" ]]; then
    log_error "Application directory $APP_DIR does not exist"
    log_info "Please ensure MicroBlog is properly installed"
    exit 1
fi

# Function to check service status
check_service_status() {
    if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
        return 0  # Service is running
    else
        return 1  # Service is not running
    fi
}

# Function to create backup
create_backup() {
    if [[ "$DO_BACKUP" == "true" ]]; then
        log_info "Creating backup..."

        mkdir -p "$BACKUP_DIR"

        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_NAME="backup_${TIMESTAMP}"
        BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

        # Create backup directory
        mkdir -p "$BACKUP_PATH"

        # Backup current build if it exists
        if [[ -d "$APP_DIR/build" ]]; then
            log_info "Backing up build directory..."
            cp -r "$APP_DIR/build" "$BACKUP_PATH/"
            if [[ $VERBOSE == "true" ]]; then
                log_info "Build backup: $BACKUP_PATH/build"
            fi
        fi

        # Backup database if it exists
        if [[ -f "$APP_DIR/microblog.db" ]]; then
            log_info "Backing up database..."
            cp "$APP_DIR/microblog.db" "$BACKUP_PATH/"
            if [[ $VERBOSE == "true" ]]; then
                log_info "Database backup: $BACKUP_PATH/microblog.db"
            fi
        fi

        # Backup configuration if it exists
        if [[ -f "$APP_DIR/config.yaml" ]]; then
            log_info "Backing up configuration..."
            cp "$APP_DIR/config.yaml" "$BACKUP_PATH/"
            if [[ $VERBOSE == "true" ]]; then
                log_info "Config backup: $BACKUP_PATH/config.yaml"
            fi
        fi

        # Backup content directory if it exists
        if [[ -d "$APP_DIR/content" ]]; then
            log_info "Backing up content directory..."
            cp -r "$APP_DIR/content" "$BACKUP_PATH/"
            if [[ $VERBOSE == "true" ]]; then
                log_info "Content backup: $BACKUP_PATH/content"
            fi
        fi

        # Clean up old backups (keep last 10)
        log_info "Cleaning up old backups..."
        cd "$BACKUP_DIR"
        ls -t backup_* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true

        log_success "Backup created: $BACKUP_PATH"
    else
        log_warning "Backup skipped as requested"
    fi
}

# Function to update application code
update_application() {
    log_info "Updating application code..."

    cd "$APP_DIR"

    # Check if this is a git repository
    if [[ -d ".git" ]]; then
        log_info "Pulling latest changes from git..."
        sudo -u "$APP_USER" git pull origin main
        if [[ $VERBOSE == "true" ]]; then
            log_info "Git pull completed"
        fi
    else
        log_warning "Not a git repository, skipping git pull"
        log_info "Manual code update may be required"
    fi

    # Install/update dependencies
    log_info "Installing/updating dependencies..."
    if [[ -f ".venv/bin/pip" ]]; then
        sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt
        if [[ $VERBOSE == "true" ]]; then
            log_info "Dependencies updated via virtual environment"
        fi
    else
        log_warning "Virtual environment not found, attempting system pip"
        pip install -r requirements.txt
    fi
}

# Function to run database migrations
run_migrations() {
    log_info "Checking for database migrations..."

    cd "$APP_DIR"

    # Check if the CLI command supports database upgrades
    if sudo -u "$APP_USER" .venv/bin/microblog --help | grep -q "upgrade-db" 2>/dev/null; then
        log_info "Running database migrations..."
        sudo -u "$APP_USER" .venv/bin/microblog upgrade-db
        if [[ $VERBOSE == "true" ]]; then
            log_info "Database migrations completed"
        fi
    else
        log_info "No database migration command available, skipping"
    fi
}

# Function to build the site
build_site() {
    if [[ "$DO_BUILD" == "true" ]]; then
        log_info "Building static site..."

        cd "$APP_DIR"

        # Use custom config if provided
        BUILD_CMD=".venv/bin/microblog build"
        if [[ -n "$CONFIG_PATH" ]]; then
            BUILD_CMD="$BUILD_CMD --config $CONFIG_PATH"
        fi

        if [[ $VERBOSE == "true" ]]; then
            BUILD_CMD="$BUILD_CMD --verbose"
        fi

        # Run build as application user
        sudo -u "$APP_USER" $BUILD_CMD

        log_success "Site build completed"
    else
        log_warning "Site build skipped as requested"
    fi
}

# Function to restart services
restart_services() {
    log_info "Restarting services..."

    # Check if service was running before restart
    SERVICE_WAS_RUNNING=false
    if check_service_status; then
        SERVICE_WAS_RUNNING=true
    fi

    # Restart MicroBlog service
    if systemctl is-enabled --quiet "$SYSTEMD_SERVICE" 2>/dev/null; then
        log_info "Restarting $SYSTEMD_SERVICE..."
        systemctl restart "$SYSTEMD_SERVICE"

        # Wait a moment for service to start
        sleep 2

        # Check if service started successfully
        if check_service_status; then
            log_success "$SYSTEMD_SERVICE restarted successfully"
        else
            log_error "$SYSTEMD_SERVICE failed to start"
            # Show service status for debugging
            systemctl status "$SYSTEMD_SERVICE" --no-pager || true
            return 1
        fi
    else
        log_warning "$SYSTEMD_SERVICE is not enabled, skipping restart"
    fi

    # Restart nginx if it's running
    if systemctl is-active --quiet nginx; then
        log_info "Restarting nginx..."
        systemctl restart nginx

        # Wait a moment for nginx to start
        sleep 1

        if systemctl is-active --quiet nginx; then
            log_success "nginx restarted successfully"
        else
            log_error "nginx failed to start"
            systemctl status nginx --no-pager || true
            return 1
        fi
    else
        log_info "nginx is not running, skipping restart"
    fi
}

# Function to verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check if MicroBlog service is running
    if check_service_status; then
        log_success "$SYSTEMD_SERVICE is running"
    else
        log_error "$SYSTEMD_SERVICE is not running"
        return 1
    fi

    # Check if build directory exists and has content
    if [[ -d "$APP_DIR/build" && "$(ls -A $APP_DIR/build)" ]]; then
        log_success "Build directory exists and contains files"
    else
        log_warning "Build directory is empty or missing"
    fi

    # Test HTTP endpoint if possible
    if command -v curl >/dev/null 2>&1; then
        log_info "Testing HTTP endpoint..."
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "HTTP endpoint is responding"
        else
            log_warning "HTTP endpoint test failed (this may be normal if health endpoint doesn't exist)"
        fi
    fi

    log_success "Deployment verification completed"
}

# Main deployment process
main() {
    log_info "Starting MicroBlog deployment..."
    log_info "Target directory: $APP_DIR"

    if [[ $VERBOSE == "true" ]]; then
        log_info "Verbose mode enabled"
        log_info "Backup: $DO_BACKUP"
        log_info "Build: $DO_BUILD"
        if [[ -n "$CONFIG_PATH" ]]; then
            log_info "Config: $CONFIG_PATH"
        fi
    fi

    # Execute deployment steps
    create_backup
    update_application
    run_migrations
    build_site
    restart_services
    verify_deployment

    log_success "Deployment completed successfully!"
    log_info "MicroBlog is now running at the configured address"

    # Show final status
    if [[ $VERBOSE == "true" ]]; then
        echo ""
        log_info "Service status:"
        systemctl status "$SYSTEMD_SERVICE" --no-pager --lines=5 || true

        if systemctl is-active --quiet nginx; then
            log_info "nginx status:"
            systemctl status nginx --no-pager --lines=3 || true
        fi
    fi
}

# Trap to handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main deployment process
main

exit 0