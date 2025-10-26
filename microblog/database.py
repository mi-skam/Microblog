"""
Database initialization and management utilities.

This module provides database setup, initialization, and utility functions
for the SQLite-based authentication system.
"""

import logging
from pathlib import Path
from typing import Optional

from microblog.auth.models import User
from microblog.auth.password import hash_password
from microblog.utils import ensure_directory, get_project_root

logger = logging.getLogger(__name__)


def get_database_path() -> Path:
    """
    Get the path to the SQLite database file.

    Returns:
        Path to microblog.db in project root
    """
    return get_project_root() / "microblog.db"


def init_database(db_path: Optional[Path] = None) -> bool:
    """
    Initialize the database with required tables.

    Args:
        db_path: Optional custom database path. Uses default if None.

    Returns:
        True if initialization successful, False otherwise
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        # Ensure the directory exists
        ensure_directory(db_path.parent)

        # Create the users table
        User.create_table(db_path)

        logger.info(f"Database initialized successfully at {db_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def create_admin_user(
    username: str,
    email: str,
    password: str,
    db_path: Optional[Path] = None
) -> Optional[User]:
    """
    Create the admin user if none exists.

    Args:
        username: Admin username
        email: Admin email
        password: Plain text password (will be hashed)
        db_path: Optional custom database path

    Returns:
        User instance if created successfully, None otherwise

    Raises:
        ValueError: If user already exists or validation fails
    """
    if db_path is None:
        db_path = get_database_path()

    # Validate inputs
    if not username or not email or not password:
        raise ValueError("Username, email, and password are required")

    if len(username) > 50:
        raise ValueError("Username must be 50 characters or less")

    if len(email) > 255:
        raise ValueError("Email must be 255 characters or less")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    try:
        # Hash the password
        password_hash = hash_password(password)

        # Create the user
        user = User.create_user(username, email, password_hash, db_path)

        if user:
            logger.info(f"Admin user '{username}' created successfully")
        else:
            logger.warning("Failed to create admin user - may already exist")

        return user

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise


def get_admin_user(db_path: Optional[Path] = None) -> Optional[User]:
    """
    Get the admin user from the database.

    Args:
        db_path: Optional custom database path

    Returns:
        User instance if found, None otherwise
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        # Since we only have one admin user, we can search by role
        # But for simplicity, let's just check if any user exists
        if User.user_exists(db_path):
            # Get the first (and only) user - we could query by role but
            # since there's only one user, this is simpler
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM users LIMIT 1")
                row = cursor.fetchone()

                if row:
                    return User(
                        user_id=row["user_id"],
                        username=row["username"],
                        email=row["email"],
                        password_hash=row["password_hash"],
                        role=row["role"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
        return None

    except Exception as e:
        logger.error(f"Error retrieving admin user: {e}")
        return None


def database_exists(db_path: Optional[Path] = None) -> bool:
    """
    Check if the database file exists.

    Args:
        db_path: Optional custom database path

    Returns:
        True if database file exists, False otherwise
    """
    if db_path is None:
        db_path = get_database_path()

    return db_path.exists()


def setup_database_if_needed(db_path: Optional[Path] = None) -> bool:
    """
    Set up the database if it doesn't exist or is incomplete.

    Args:
        db_path: Optional custom database path

    Returns:
        True if setup successful or not needed, False if setup failed
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        # Always initialize (create tables if they don't exist)
        if not init_database(db_path):
            return False

        logger.info("Database setup completed")
        return True

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


def reset_database(db_path: Optional[Path] = None) -> bool:
    """
    Reset the database by removing it (for development/testing).

    Args:
        db_path: Optional custom database path

    Returns:
        True if reset successful, False otherwise
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        if db_path.exists():
            db_path.unlink()
            logger.info(f"Database reset: {db_path} removed")

        return True

    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False


def get_database_info(db_path: Optional[Path] = None) -> dict:
    """
    Get information about the database state.

    Args:
        db_path: Optional custom database path

    Returns:
        Dictionary with database information
    """
    if db_path is None:
        db_path = get_database_path()

    info = {
        "database_path": str(db_path),
        "exists": database_exists(db_path),
        "admin_user_exists": False,
        "admin_username": None,
        "error": None
    }

    if info["exists"]:
        try:
            info["admin_user_exists"] = User.user_exists(db_path)
            if info["admin_user_exists"]:
                admin_user = get_admin_user(db_path)
                if admin_user:
                    info["admin_username"] = admin_user.username
        except Exception as e:
            info["error"] = str(e)

    return info