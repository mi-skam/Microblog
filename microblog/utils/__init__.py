"""
Utilities package for microblog application.

This package provides common utilities including logging, monitoring, and helper functions.
"""

import shutil
from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def safe_copy_file(src: Path, dest: Path) -> bool:
    """Safely copy a file, ensuring the destination directory exists."""
    try:
        ensure_directory(dest.parent)
        shutil.copy2(src, dest)
        return True
    except Exception:
        return False


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_content_dir() -> Path:
    """Get the content directory path."""
    return get_project_root() / "content"


def get_build_dir() -> Path:
    """Get the build directory path."""
    return get_project_root() / "build"


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    return get_project_root() / "templates"


def get_static_dir() -> Path:
    """Get the static directory path."""
    return get_project_root() / "static"


__all__ = [
    "ensure_directory",
    "get_build_dir",
    "get_content_dir",
    "get_project_root",
    "get_static_dir",
    "get_templates_dir",
    "safe_copy_file",
]