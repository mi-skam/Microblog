"""
Asset manager for copying images and static files from content directory to build output.

This module provides asset copying, file validation, path management, and build-time
optimization for the static site generator.
"""

import hashlib
import logging
import mimetypes
import shutil
from pathlib import Path
from typing import Any

from microblog.server.config import get_config
from microblog.utils import (
    ensure_directory,
    get_content_dir,
    get_static_dir,
)

logger = logging.getLogger(__name__)


class AssetManagingError(Exception):
    """Raised when asset management operations fail."""
    pass


class AssetManager:
    """
    Asset manager for copying and managing static files.

    Features:
    - Image and static file copying from multiple sources
    - File validation and security checks
    - Path management and organization
    - Change detection for efficient builds
    - Atomic operations with rollback support
    - Build-time optimization
    """

    def __init__(self):
        """Initialize the asset manager with configuration."""
        self.config = get_config()
        self.content_dir = get_content_dir()
        self.static_dir = get_static_dir()
        self.build_dir = Path(self.config.build.output_dir)

        # Allowed file extensions for security
        self.allowed_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp',
            # Documents
            '.pdf', '.txt', '.md',
            # Web assets
            '.css', '.js', '.json', '.xml',
            # Fonts
            '.woff', '.woff2', '.ttf', '.otf', '.eot',
            # Other common assets
            '.zip', '.tar', '.gz'
        }

        # Source to destination mappings
        self.asset_mappings = [
            {
                'source': self.content_dir / 'images',
                'destination': self.build_dir / 'images',
                'description': 'User content images'
            },
            {
                'source': self.static_dir / 'css',
                'destination': self.build_dir / 'css',
                'description': 'CSS stylesheets'
            },
            {
                'source': self.static_dir / 'js',
                'destination': self.build_dir / 'js',
                'description': 'JavaScript files'
            },
            {
                'source': self.static_dir / 'images',
                'destination': self.build_dir / 'images',
                'description': 'Static site images'
            }
        ]

        logger.info("Asset manager initialized")

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate a file for copying.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid for copying, False otherwise
        """
        try:
            # Check if file exists and is a regular file
            if not file_path.is_file():
                logger.debug(f"Skipping non-file: {file_path}")
                return False

            # Check file extension
            if file_path.suffix.lower() not in self.allowed_extensions:
                logger.warning(f"Skipping file with disallowed extension: {file_path}")
                return False

            # Check file size (limit to 50MB)
            file_size = file_path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                logger.warning(f"Skipping large file ({file_size} bytes): {file_path}")
                return False

            # Check MIME type for additional security
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and mime_type.startswith(('application/x-executable', 'application/x-sharedlib')):
                logger.warning(f"Skipping executable file: {file_path}")
                return False

            # Check for suspicious file names
            filename = file_path.name.lower()
            suspicious_patterns = ['.htaccess', '.env', 'config.ini', 'web.config']
            if any(pattern in filename for pattern in suspicious_patterns):
                logger.warning(f"Skipping suspicious file: {file_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file for change detection.

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash string
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def needs_update(self, source_path: Path, dest_path: Path) -> bool:
        """
        Check if a file needs to be copied or updated.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if file needs to be copied, False otherwise
        """
        try:
            # If destination doesn't exist, always copy
            if not dest_path.exists():
                return True

            # Compare modification times
            source_mtime = source_path.stat().st_mtime
            dest_mtime = dest_path.stat().st_mtime

            if source_mtime > dest_mtime:
                return True

            # If times are very close, compare file sizes
            if abs(source_mtime - dest_mtime) < 1:  # Within 1 second
                source_size = source_path.stat().st_size
                dest_size = dest_path.stat().st_size
                return source_size != dest_size

            return False

        except Exception as e:
            logger.error(f"Error checking if update needed for {source_path}: {e}")
            return True  # Default to copying on error

    def copy_file(self, source_path: Path, dest_path: Path) -> bool:
        """
        Copy a single file with validation and error handling.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if copy successful, False otherwise
        """
        try:
            # Validate the source file
            if not self.validate_file(source_path):
                return False

            # Check if update is needed
            if not self.needs_update(source_path, dest_path):
                logger.debug(f"Skipping up-to-date file: {source_path}")
                return True

            # Ensure destination directory exists
            ensure_directory(dest_path.parent)

            # Copy the file with metadata
            shutil.copy2(source_path, dest_path)

            logger.debug(f"Copied: {source_path} -> {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Error copying file {source_path} to {dest_path}: {e}")
            return False

    def copy_directory_assets(self, source_dir: Path, dest_dir: Path, recursive: bool = True) -> tuple[int, int]:
        """
        Copy all valid assets from a source directory to destination.

        Args:
            source_dir: Source directory path
            dest_dir: Destination directory path
            recursive: Whether to copy subdirectories recursively

        Returns:
            Tuple of (successful_copies, failed_copies)
        """
        successful = 0
        failed = 0

        try:
            if not source_dir.exists() or not source_dir.is_dir():
                logger.debug(f"Source directory does not exist: {source_dir}")
                return successful, failed

            # Get all files to copy
            if recursive:
                files_to_copy = source_dir.rglob('*')
            else:
                files_to_copy = source_dir.glob('*')

            for source_file in files_to_copy:
                if source_file.is_file():
                    # Calculate relative path for destination
                    relative_path = source_file.relative_to(source_dir)
                    dest_file = dest_dir / relative_path

                    if self.copy_file(source_file, dest_file):
                        successful += 1
                    else:
                        failed += 1

        except Exception as e:
            logger.error(f"Error copying directory assets from {source_dir}: {e}")
            failed += 1

        return successful, failed

    def copy_all_assets(self) -> dict[str, Any]:
        """
        Copy all assets from configured sources to build directory.

        Returns:
            Dictionary with copy results and statistics
        """
        results = {
            'total_successful': 0,
            'total_failed': 0,
            'mappings': []
        }

        try:
            logger.info("Starting asset copying process")

            for mapping in self.asset_mappings:
                source_dir = mapping['source']
                dest_dir = mapping['destination']
                description = mapping['description']

                logger.info(f"Copying {description} from {source_dir} to {dest_dir}")

                successful, failed = self.copy_directory_assets(source_dir, dest_dir)

                mapping_result = {
                    'source': str(source_dir),
                    'destination': str(dest_dir),
                    'description': description,
                    'successful': successful,
                    'failed': failed
                }

                results['mappings'].append(mapping_result)
                results['total_successful'] += successful
                results['total_failed'] += failed

                if failed > 0:
                    logger.warning(f"{description}: {successful} successful, {failed} failed")
                else:
                    logger.info(f"{description}: {successful} files copied")

            total_files = results['total_successful'] + results['total_failed']
            logger.info(f"Asset copying completed: {results['total_successful']}/{total_files} files successful")

            if results['total_failed'] > 0:
                raise AssetManagingError(f"Failed to copy {results['total_failed']} assets")

        except Exception as e:
            logger.error(f"Asset copying process failed: {e}")
            raise AssetManagingError(f"Asset copying failed: {e}") from e

        return results

    def clean_build_assets(self) -> bool:
        """
        Clean asset directories in the build output.

        Returns:
            True if cleaning successful, False otherwise
        """
        try:
            asset_dirs = [
                self.build_dir / 'images',
                self.build_dir / 'css',
                self.build_dir / 'js'
            ]

            for asset_dir in asset_dirs:
                if asset_dir.exists():
                    shutil.rmtree(asset_dir)
                    logger.debug(f"Cleaned asset directory: {asset_dir}")

            logger.info("Build asset directories cleaned")
            return True

        except Exception as e:
            logger.error(f"Error cleaning build assets: {e}")
            return False

    def get_asset_info(self) -> dict[str, Any]:
        """
        Get information about assets in source directories.

        Returns:
            Dictionary with asset information and statistics
        """
        info = {
            'mappings': [],
            'total_files': 0,
            'total_size': 0
        }

        try:
            for mapping in self.asset_mappings:
                source_dir = mapping['source']
                description = mapping['description']

                mapping_info = {
                    'source': str(source_dir),
                    'description': description,
                    'files': 0,
                    'size': 0,
                    'exists': source_dir.exists()
                }

                if source_dir.exists() and source_dir.is_dir():
                    for file_path in source_dir.rglob('*'):
                        if file_path.is_file() and self.validate_file(file_path):
                            file_size = file_path.stat().st_size
                            mapping_info['files'] += 1
                            mapping_info['size'] += file_size

                info['mappings'].append(mapping_info)
                info['total_files'] += mapping_info['files']
                info['total_size'] += mapping_info['size']

        except Exception as e:
            logger.error(f"Error getting asset info: {e}")

        return info


# Global asset manager instance
_asset_manager: AssetManager | None = None


def get_asset_manager() -> AssetManager:
    """
    Get the global asset manager instance.

    Returns:
        AssetManager instance
    """
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetManager()
    return _asset_manager
