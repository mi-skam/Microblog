"""
Image upload service with file validation, sanitization, and storage management.

This module provides secure image upload capabilities including validation,
filename sanitization, storage management, and markdown snippet generation.
"""

import logging
import re
import secrets
from pathlib import Path
from typing import Any, BinaryIO

from microblog.builder.asset_manager import get_asset_manager
from microblog.utils import ensure_directory, get_content_dir

logger = logging.getLogger(__name__)


class ImageUploadError(Exception):
    """Raised when image upload operations fail."""
    pass


class ImageValidationError(Exception):
    """Raised when image validation fails."""
    pass


class ImageService:
    """
    Image upload and management service.

    Features:
    - Secure file validation using AssetManager
    - Filename sanitization and collision handling
    - Storage management in content/images/
    - Markdown snippet generation
    - Progress feedback support
    """

    def __init__(self):
        """Initialize the image service."""
        self.asset_manager = get_asset_manager()
        self.content_dir = get_content_dir()
        self.images_dir = self.content_dir / "images"

        # Ensure images directory exists
        ensure_directory(self.images_dir)

        logger.info("Image service initialized")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename for security and compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        if not filename:
            return "image"

        # Get the file extension and base name
        path = Path(filename)
        base_name = path.stem
        extension = path.suffix.lower()

        # Remove or replace dangerous characters
        # Keep only alphanumeric, hyphens, underscores, and dots
        sanitized_base = re.sub(r'[^\w\-_.]', '_', base_name)

        # Remove consecutive underscores only (preserve dots for file extensions)
        sanitized_base = re.sub(r'_+', '_', sanitized_base)

        # Remove leading/trailing underscores and dots
        sanitized_base = sanitized_base.strip('_.')

        # Ensure we have a base name
        if not sanitized_base:
            sanitized_base = "image"

        # Limit length
        if len(sanitized_base) > 100:
            sanitized_base = sanitized_base[:100]

        return f"{sanitized_base}{extension}"

    def generate_unique_filename(self, filename: str) -> str:
        """
        Generate a unique filename to avoid collisions.

        Args:
            filename: Desired filename

        Returns:
            Unique filename that doesn't exist in the images directory
        """
        sanitized = self.sanitize_filename(filename)
        path = Path(sanitized)
        base_name = path.stem
        extension = path.suffix

        # Check if file already exists
        target_path = self.images_dir / sanitized
        if not target_path.exists():
            return sanitized

        # Generate unique name with random suffix
        counter = 1
        while True:
            # Try with counter first
            new_name = f"{base_name}_{counter}{extension}"
            target_path = self.images_dir / new_name
            if not target_path.exists():
                return new_name

            counter += 1

            # After 100 attempts, use random suffix
            if counter > 100:
                random_suffix = secrets.token_hex(4)
                new_name = f"{base_name}_{random_suffix}{extension}"
                target_path = self.images_dir / new_name
                if not target_path.exists():
                    return new_name
                counter = 1  # Reset counter for another round

    def validate_image_file(self, file_path: Path) -> bool:
        """
        Validate an image file using the AssetManager's validation.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid, False otherwise

        Raises:
            ImageValidationError: If validation fails with specific error
        """
        try:
            # Use AssetManager's comprehensive validation
            if not self.asset_manager.validate_file(file_path):
                raise ImageValidationError("File failed security validation")

            # Additional check to ensure it's an image
            extension = file_path.suffix.lower()
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp'}

            if extension not in image_extensions:
                raise ImageValidationError(f"File extension '{extension}' is not allowed for images")

            return True

        except ImageValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating image file {file_path}: {e}")
            raise ImageValidationError(f"Validation failed: {str(e)}") from e

    def save_uploaded_file(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """
        Save uploaded file content to the images directory.

        Args:
            file_content: Binary content of the file
            filename: Original filename

        Returns:
            Dictionary with save results including path and markdown snippet

        Raises:
            ImageUploadError: If save operation fails
            ImageValidationError: If file validation fails
        """
        try:
            # Generate unique filename
            unique_filename = self.generate_unique_filename(filename)
            target_path = self.images_dir / unique_filename

            # Write file temporarily for validation
            temp_path = target_path.with_suffix(target_path.suffix + '.tmp')
            try:
                with open(temp_path, 'wb') as f:
                    f.write(file_content)

                # Validate the temporary file
                self.validate_image_file(temp_path)

                # Move to final location
                temp_path.rename(target_path)

                logger.info(f"Image saved successfully: {target_path}")

                # Generate relative URL for markdown
                relative_url = f"/images/{unique_filename}"
                markdown_snippet = f"![{Path(filename).stem}]({relative_url})"

                return {
                    'filename': unique_filename,
                    'path': str(target_path),
                    'relative_path': str(target_path.relative_to(self.content_dir)),
                    'url': relative_url,
                    'markdown': markdown_snippet,
                    'size': len(file_content)
                }

            except Exception:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                raise

        except ImageValidationError:
            raise
        except Exception as e:
            logger.error(f"Error saving uploaded file '{filename}': {e}")
            raise ImageUploadError(f"Failed to save file: {str(e)}") from e

    async def save_uploaded_file_async(self, file_object: BinaryIO, filename: str) -> dict[str, Any]:
        """
        Save uploaded file from a file object (async version).

        Args:
            file_object: File object to read from
            filename: Original filename

        Returns:
            Dictionary with save results including path and markdown snippet
        """
        try:
            # Read file content
            file_content = file_object.read()

            # Reset file pointer in case it's needed elsewhere
            file_object.seek(0)

            return self.save_uploaded_file(file_content, filename)

        except Exception as e:
            logger.error(f"Error saving uploaded file object '{filename}': {e}")
            raise ImageUploadError(f"Failed to save file: {str(e)}") from e

    def delete_image(self, filename: str) -> bool:
        """
        Delete an image from the images directory.

        Args:
            filename: Name of the file to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            image_path = self.images_dir / filename

            if not image_path.exists():
                logger.warning(f"Attempted to delete non-existent image: {filename}")
                return False

            # Basic security check - ensure file is within images directory
            if not str(image_path.resolve()).startswith(str(self.images_dir.resolve())):
                logger.error(f"Attempted to delete file outside images directory: {filename}")
                return False

            image_path.unlink()
            logger.info(f"Image deleted successfully: {filename}")
            return True

        except Exception as e:
            logger.error(f"Error deleting image '{filename}': {e}")
            return False

    def list_images(self) -> list[dict[str, Any]]:
        """
        List all images in the images directory.

        Returns:
            List of dictionaries with image information
        """
        images = []

        try:
            if not self.images_dir.exists():
                return images

            for image_path in self.images_dir.glob('*'):
                if image_path.is_file() and self.asset_manager.validate_file(image_path):
                    try:
                        stat = image_path.stat()
                        relative_url = f"/images/{image_path.name}"

                        images.append({
                            'filename': image_path.name,
                            'path': str(image_path),
                            'relative_path': str(image_path.relative_to(self.content_dir)),
                            'url': relative_url,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        })
                    except Exception as e:
                        logger.error(f"Error getting info for image {image_path}: {e}")

            # Sort by modification time, newest first
            images.sort(key=lambda x: x['modified'], reverse=True)

        except Exception as e:
            logger.error(f"Error listing images: {e}")

        return images

    def get_image_info(self, filename: str) -> dict[str, Any] | None:
        """
        Get information about a specific image.

        Args:
            filename: Name of the image file

        Returns:
            Dictionary with image information or None if not found
        """
        try:
            image_path = self.images_dir / filename

            if not image_path.exists() or not image_path.is_file():
                return None

            if not self.asset_manager.validate_file(image_path):
                return None

            stat = image_path.stat()
            relative_url = f"/images/{filename}"

            return {
                'filename': filename,
                'path': str(image_path),
                'relative_path': str(image_path.relative_to(self.content_dir)),
                'url': relative_url,
                'size': stat.st_size,
                'modified': stat.st_mtime
            }

        except Exception as e:
            logger.error(f"Error getting image info for '{filename}': {e}")
            return None


# Global image service instance
_image_service: ImageService | None = None


def get_image_service() -> ImageService:
    """
    Get the global image service instance.

    Returns:
        ImageService instance
    """
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
