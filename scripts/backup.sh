#!/bin/bash
# Backup script for MicroBlog
# Usage: ./scripts/backup.sh [--compress] [--remote] [--config CONFIG_PATH]

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_NAME="microblog"
APP_DIR="/opt/microblog"
BACKUP_DIR="$APP_DIR/backups"
DEFAULT_RETENTION_DAYS=30

# Default options
COMPRESS_BACKUP=false
REMOTE_BACKUP=false
CONFIG_PATH=""
VERBOSE=false
RETENTION_DAYS=$DEFAULT_RETENTION_DAYS

# Remote backup configuration (can be overridden by config file)
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PATH=""
REMOTE_KEY=""

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
        --compress|-c)
            COMPRESS_BACKUP=true
            shift
            ;;
        --remote|-r)
            REMOTE_BACKUP=true
            shift
            ;;
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Create backup of MicroBlog data"
            echo ""
            echo "Options:"
            echo "  --compress, -c    Create compressed backup archive"
            echo "  --remote, -r      Upload backup to remote location"
            echo "  --config PATH     Use specific configuration file for backup settings"
            echo "  --retention DAYS  Number of days to retain backups (default: $DEFAULT_RETENTION_DAYS)"
            echo "  --verbose, -v     Enable verbose output"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Remote backup requires configuration file with:"
            echo "  backup.remote.host, backup.remote.user, backup.remote.path, backup.remote.key"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Load backup configuration if provided
load_backup_config() {
    if [[ -n "$CONFIG_PATH" && -f "$CONFIG_PATH" ]]; then
        log_info "Loading backup configuration from $CONFIG_PATH"

        # This is a simple implementation - in a real scenario, you might want to use yq or similar
        if command -v python3 >/dev/null 2>&1; then
            # Try to extract backup config using Python
            BACKUP_CONFIG=$(python3 -c "
import yaml
import sys
try:
    with open('$CONFIG_PATH', 'r') as f:
        config = yaml.safe_load(f)
    backup = config.get('backup', {})
    remote = backup.get('remote', {})
    print(f\"REMOTE_HOST={remote.get('host', '')}\")
    print(f\"REMOTE_USER={remote.get('user', '')}\")
    print(f\"REMOTE_PATH={remote.get('path', '')}\")
    print(f\"REMOTE_KEY={remote.get('key', '')}\")
    print(f\"RETENTION_DAYS={backup.get('retention_days', $DEFAULT_RETENTION_DAYS)}\")
except Exception as e:
    print(f\"ERROR: {e}\", file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || true)

            if [[ -n "$BACKUP_CONFIG" ]]; then
                eval "$BACKUP_CONFIG"
                if [[ $VERBOSE == "true" ]]; then
                    log_info "Remote backup configuration loaded"
                fi
            fi
        else
            log_warning "Python3 not available, cannot parse YAML configuration"
        fi
    elif [[ -n "$CONFIG_PATH" ]]; then
        log_warning "Configuration file not found: $CONFIG_PATH"
    fi
}

# Function to create backup directory structure
create_backup_structure() {
    local backup_path="$1"
    local timestamp="$2"

    mkdir -p "$backup_path"

    # Create manifest file
    cat > "$backup_path/backup_manifest.txt" << EOF
MicroBlog Backup Manifest
========================
Backup Date: $(date -Iseconds)
Backup Path: $backup_path
Backup Type: $(if [[ $COMPRESS_BACKUP == "true" ]]; then echo "Compressed"; else echo "Directory"; fi)
Remote Copy: $(if [[ $REMOTE_BACKUP == "true" ]]; then echo "Yes"; else echo "No"; fi)

Contents:
EOF

    echo "$backup_path"
}

# Function to backup database
backup_database() {
    local backup_path="$1"

    if [[ -f "$APP_DIR/microblog.db" ]]; then
        log_info "Backing up SQLite database..."

        # Create atomic backup using SQLite backup command if available
        if command -v sqlite3 >/dev/null 2>&1; then
            sqlite3 "$APP_DIR/microblog.db" ".backup '$backup_path/microblog.db'"
            log_success "Database backed up atomically"
        else
            # Fallback to file copy
            cp "$APP_DIR/microblog.db" "$backup_path/"
            log_success "Database backed up (file copy)"
        fi

        echo "- Database: microblog.db" >> "$backup_path/backup_manifest.txt"

        if [[ $VERBOSE == "true" ]]; then
            DB_SIZE=$(du -h "$backup_path/microblog.db" | cut -f1)
            log_info "Database backup size: $DB_SIZE"
        fi
    else
        log_warning "Database file not found, skipping database backup"
        echo "- Database: NOT FOUND" >> "$backup_path/backup_manifest.txt"
    fi
}

# Function to backup content directory
backup_content() {
    local backup_path="$1"

    if [[ -d "$APP_DIR/content" ]]; then
        log_info "Backing up content directory..."

        # Create content backup with proper permissions
        cp -r "$APP_DIR/content" "$backup_path/"

        # Count files for manifest
        POST_COUNT=$(find "$backup_path/content/posts" -name "*.md" 2>/dev/null | wc -l || echo "0")
        PAGE_COUNT=$(find "$backup_path/content/pages" -name "*.md" 2>/dev/null | wc -l || echo "0")
        IMAGE_COUNT=$(find "$backup_path/content/images" -type f 2>/dev/null | wc -l || echo "0")

        echo "- Content directory: content/" >> "$backup_path/backup_manifest.txt"
        echo "  - Posts: $POST_COUNT files" >> "$backup_path/backup_manifest.txt"
        echo "  - Pages: $PAGE_COUNT files" >> "$backup_path/backup_manifest.txt"
        echo "  - Images: $IMAGE_COUNT files" >> "$backup_path/backup_manifest.txt"

        log_success "Content directory backed up"

        if [[ $VERBOSE == "true" ]]; then
            CONTENT_SIZE=$(du -sh "$backup_path/content" | cut -f1)
            log_info "Content backup size: $CONTENT_SIZE"
            log_info "Posts: $POST_COUNT, Pages: $PAGE_COUNT, Images: $IMAGE_COUNT"
        fi
    else
        log_warning "Content directory not found, skipping content backup"
        echo "- Content directory: NOT FOUND" >> "$backup_path/backup_manifest.txt"
    fi
}

# Function to backup build directory
backup_build() {
    local backup_path="$1"

    if [[ -d "$APP_DIR/build" && "$(ls -A $APP_DIR/build 2>/dev/null)" ]]; then
        log_info "Backing up build directory..."

        cp -r "$APP_DIR/build" "$backup_path/"

        # Count files for manifest
        BUILD_FILE_COUNT=$(find "$backup_path/build" -type f 2>/dev/null | wc -l || echo "0")

        echo "- Build directory: build/" >> "$backup_path/backup_manifest.txt"
        echo "  - Generated files: $BUILD_FILE_COUNT files" >> "$backup_path/backup_manifest.txt"

        log_success "Build directory backed up"

        if [[ $VERBOSE == "true" ]]; then
            BUILD_SIZE=$(du -sh "$backup_path/build" | cut -f1)
            log_info "Build backup size: $BUILD_SIZE"
            log_info "Generated files: $BUILD_FILE_COUNT"
        fi
    else
        log_warning "Build directory is empty or missing, skipping build backup"
        echo "- Build directory: EMPTY OR NOT FOUND" >> "$backup_path/backup_manifest.txt"
    fi
}

# Function to backup configuration
backup_configuration() {
    local backup_path="$1"

    # Backup main config if it exists
    if [[ -f "$APP_DIR/config.yaml" ]]; then
        log_info "Backing up configuration files..."
        cp "$APP_DIR/config.yaml" "$backup_path/"
        echo "- Configuration: config.yaml" >> "$backup_path/backup_manifest.txt"
    fi

    # Backup content config if it exists
    if [[ -f "$APP_DIR/content/_data/config.yaml" ]]; then
        mkdir -p "$backup_path/content/_data"
        cp "$APP_DIR/content/_data/config.yaml" "$backup_path/content/_data/"
        echo "- Site configuration: content/_data/config.yaml" >> "$backup_path/backup_manifest.txt"
    fi

    # Backup any systemd service files
    SYSTEMD_FILE="/etc/systemd/system/microblog.service"
    if [[ -f "$SYSTEMD_FILE" ]]; then
        mkdir -p "$backup_path/systemd"
        cp "$SYSTEMD_FILE" "$backup_path/systemd/"
        echo "- Systemd service: microblog.service" >> "$backup_path/backup_manifest.txt"
    fi

    # Backup nginx configuration if it exists
    NGINX_CONFIGS=("/etc/nginx/sites-available/microblog" "/etc/nginx/sites-enabled/microblog")
    for nginx_config in "${NGINX_CONFIGS[@]}"; do
        if [[ -f "$nginx_config" ]]; then
            mkdir -p "$backup_path/nginx"
            cp "$nginx_config" "$backup_path/nginx/$(basename "$nginx_config")"
            echo "- Nginx config: $(basename "$nginx_config")" >> "$backup_path/backup_manifest.txt"
        fi
    done

    log_success "Configuration backup completed"
}

# Function to create compressed archive
create_compressed_archive() {
    local backup_path="$1"
    local timestamp="$2"

    if [[ $COMPRESS_BACKUP == "true" ]]; then
        log_info "Creating compressed archive..."

        local archive_name="microblog_backup_${timestamp}.tar.gz"
        local archive_path="$BACKUP_DIR/$archive_name"

        # Create compressed archive
        cd "$BACKUP_DIR"
        tar -czf "$archive_name" "backup_${timestamp}/"

        # Remove uncompressed directory
        rm -rf "backup_${timestamp}/"

        log_success "Compressed archive created: $archive_name"

        if [[ $VERBOSE == "true" ]]; then
            ARCHIVE_SIZE=$(du -h "$archive_path" | cut -f1)
            log_info "Archive size: $ARCHIVE_SIZE"
        fi

        echo "$archive_path"
    else
        echo "$backup_path"
    fi
}

# Function to upload to remote location
upload_to_remote() {
    local backup_path="$1"

    if [[ $REMOTE_BACKUP == "true" ]]; then
        if [[ -z "$REMOTE_HOST" || -z "$REMOTE_USER" || -z "$REMOTE_PATH" ]]; then
            log_error "Remote backup requested but configuration incomplete"
            log_error "Required: REMOTE_HOST, REMOTE_USER, REMOTE_PATH"
            return 1
        fi

        log_info "Uploading backup to remote location..."

        # Prepare SSH options
        SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        if [[ -n "$REMOTE_KEY" && -f "$REMOTE_KEY" ]]; then
            SSH_OPTS="$SSH_OPTS -i $REMOTE_KEY"
        fi

        # Upload using rsync for efficient transfer
        if command -v rsync >/dev/null 2>&1; then
            log_info "Using rsync for remote upload..."
            rsync -avz --progress -e "ssh $SSH_OPTS" "$backup_path" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        else
            # Fallback to scp
            log_info "Using scp for remote upload..."
            scp -r $SSH_OPTS "$backup_path" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        fi

        log_success "Backup uploaded to $REMOTE_HOST:$REMOTE_PATH"

        if [[ $VERBOSE == "true" ]]; then
            log_info "Remote backup location: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$(basename "$backup_path")"
        fi
    fi
}

# Function to clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

    # Local cleanup
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
        find "$BACKUP_DIR" -type d -name "backup_*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

        REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "backup_*" -o -name "*.tar.gz" | wc -l)
        log_success "Local cleanup completed. Remaining backups: $REMAINING_BACKUPS"
    fi

    # Remote cleanup (if configured)
    if [[ $REMOTE_BACKUP == "true" && -n "$REMOTE_HOST" && -n "$REMOTE_USER" && -n "$REMOTE_PATH" ]]; then
        log_info "Cleaning up remote backups..."

        SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        if [[ -n "$REMOTE_KEY" && -f "$REMOTE_KEY" ]]; then
            SSH_OPTS="$SSH_OPTS -i $REMOTE_KEY"
        fi

        # Remote cleanup command
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "
            find '$REMOTE_PATH' -type f -name '*.tar.gz' -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
            find '$REMOTE_PATH' -type d -name 'backup_*' -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
        " || log_warning "Remote cleanup failed or partially completed"
    fi
}

# Function to verify backup integrity
verify_backup() {
    local backup_path="$1"

    log_info "Verifying backup integrity..."

    local errors=0

    # Check if backup directory exists
    if [[ ! -d "$backup_path" && ! -f "$backup_path" ]]; then
        log_error "Backup path does not exist: $backup_path"
        return 1
    fi

    # If it's a compressed archive, test it
    if [[ -f "$backup_path" && "$backup_path" =~ \.tar\.gz$ ]]; then
        if tar -tzf "$backup_path" >/dev/null 2>&1; then
            log_success "Compressed archive integrity verified"
        else
            log_error "Compressed archive is corrupted"
            ((errors++))
        fi
    fi

    # Check manifest file (if uncompressed)
    if [[ -d "$backup_path" ]]; then
        if [[ -f "$backup_path/backup_manifest.txt" ]]; then
            log_success "Backup manifest found"
        else
            log_warning "Backup manifest missing"
            ((errors++))
        fi

        # Verify database backup if expected
        if [[ -f "$APP_DIR/microblog.db" && ! -f "$backup_path/microblog.db" ]]; then
            log_error "Database backup missing"
            ((errors++))
        fi
    fi

    if [[ $errors -eq 0 ]]; then
        log_success "Backup verification completed successfully"
        return 0
    else
        log_error "Backup verification failed with $errors error(s)"
        return 1
    fi
}

# Main backup process
main() {
    log_info "Starting MicroBlog backup..."
    log_info "Target directory: $APP_DIR"

    # Load configuration
    load_backup_config

    if [[ $VERBOSE == "true" ]]; then
        log_info "Verbose mode enabled"
        log_info "Compress: $COMPRESS_BACKUP"
        log_info "Remote: $REMOTE_BACKUP"
        log_info "Retention: $RETENTION_DAYS days"
        if [[ -n "$CONFIG_PATH" ]]; then
            log_info "Config: $CONFIG_PATH"
        fi
    fi

    # Verify source directory exists
    if [[ ! -d "$APP_DIR" ]]; then
        log_error "Application directory does not exist: $APP_DIR"
        exit 1
    fi

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Generate timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="backup_${TIMESTAMP}"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

    # Create backup structure
    create_backup_structure "$BACKUP_PATH" "$TIMESTAMP"

    # Perform backup operations
    backup_database "$BACKUP_PATH"
    backup_content "$BACKUP_PATH"
    backup_build "$BACKUP_PATH"
    backup_configuration "$BACKUP_PATH"

    # Create compressed archive if requested
    FINAL_BACKUP_PATH=$(create_compressed_archive "$BACKUP_PATH" "$TIMESTAMP")

    # Verify backup
    if ! verify_backup "$FINAL_BACKUP_PATH"; then
        log_error "Backup verification failed!"
        exit 1
    fi

    # Upload to remote if requested
    upload_to_remote "$FINAL_BACKUP_PATH"

    # Clean up old backups
    cleanup_old_backups

    log_success "Backup completed successfully!"
    log_info "Backup location: $FINAL_BACKUP_PATH"

    # Show backup summary
    if [[ $VERBOSE == "true" ]]; then
        echo ""
        log_info "Backup Summary:"
        if [[ -f "$FINAL_BACKUP_PATH" ]]; then
            BACKUP_SIZE=$(du -h "$FINAL_BACKUP_PATH" | cut -f1)
            log_info "Backup size: $BACKUP_SIZE"
        else
            BACKUP_SIZE=$(du -sh "$FINAL_BACKUP_PATH" | cut -f1)
            log_info "Backup size: $BACKUP_SIZE"
        fi

        # Show manifest if available
        if [[ -f "$BACKUP_PATH/backup_manifest.txt" ]]; then
            echo ""
            cat "$BACKUP_PATH/backup_manifest.txt"
        fi
    fi
}

# Trap to handle script interruption
trap 'log_error "Backup interrupted"; exit 1' INT TERM

# Run main backup process
main

exit 0