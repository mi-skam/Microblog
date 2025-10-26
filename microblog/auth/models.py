"""
SQLite-based User model for authentication system.

This module provides the User model with SQLite database integration following
the single-admin-user pattern specified in the ERD.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class User:
    """
    User model representing the single admin user in the system.

    Based on the ERD specification with SQLite storage. Only one admin user
    is allowed in the system at any time.
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        password_hash: str,
        role: str = "admin",
        created_at: datetime | None = None,
        updated_at: datetime | None = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def create_table(cls, db_path: Path) -> None:
        """Create the users table if it doesn't exist."""
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(10) DEFAULT 'admin' NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @classmethod
    def get_by_username(cls, username: str, db_path: Path) -> User | None:
        """Get user by username."""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()

            if row:
                return cls(
                    user_id=row["user_id"],
                    username=row["username"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    created_at=cls._parse_datetime(row["created_at"]),
                    updated_at=cls._parse_datetime(row["updated_at"])
                )
            return None

    @classmethod
    def get_by_id(cls, user_id: int, db_path: Path) -> User | None:
        """Get user by ID."""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return cls(
                    user_id=row["user_id"],
                    username=row["username"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    created_at=cls._parse_datetime(row["created_at"]),
                    updated_at=cls._parse_datetime(row["updated_at"])
                )
            return None

    @classmethod
    def user_exists(cls, db_path: Path) -> bool:
        """Check if any user exists (single-user constraint)."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count > 0

    @classmethod
    def create_user(
        cls,
        username: str,
        email: str,
        password_hash: str,
        db_path: Path
    ) -> User | None:
        """
        Create a new user. Only one admin user is allowed.

        Returns:
            User instance if created successfully, None if user already exists
        """
        if cls.user_exists(db_path):
            raise ValueError("Only one admin user is allowed in the system")

        try:
            with sqlite3.connect(db_path) as conn:
                now = datetime.now(timezone.utc).isoformat()
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role, created_at, updated_at)
                    VALUES (?, ?, ?, 'admin', ?, ?)
                    """,
                    (username, email, password_hash, now, now)
                )
                user_id = cursor.lastrowid
                conn.commit()

                return cls(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role="admin",
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now)
                )
        except sqlite3.IntegrityError:
            return None

    def update_password(self, new_password_hash: str, db_path: Path) -> bool:
        """Update user password hash."""
        try:
            with sqlite3.connect(db_path) as conn:
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "UPDATE users SET password_hash = ?, updated_at = ? WHERE user_id = ?",
                    (new_password_hash, now, self.user_id)
                )
                conn.commit()
                self.password_hash = new_password_hash
                self.updated_at = datetime.fromisoformat(now)
                return True
        except sqlite3.Error:
            return False

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding password hash)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def _parse_datetime(dt_str: str) -> datetime:
        """Parse datetime string from SQLite, handling both ISO and SQLite default formats."""
        if not dt_str:
            return datetime.now(timezone.utc)

        try:
            # Try ISO format first (for manually inserted timestamps)
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try SQLite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                # Fallback to current time if parsing fails
                return datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"
