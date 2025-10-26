"""
Password hashing utilities using bcrypt.

This module provides secure password hashing and verification using bcrypt
with a minimum cost factor of 12 as specified in the requirements.
"""

import bcrypt

# Cost factor for bcrypt (minimum 12 as required)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor ≥12.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string

    Raises:
        ValueError: If password is empty
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Convert to bytes and hash with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def needs_update(hashed_password: str) -> bool:
    """
    Check if password hash needs updating (e.g., if cost factor is too low).

    Args:
        hashed_password: Previously hashed password to check

    Returns:
        True if hash needs updating, False otherwise
    """
    try:
        if not hashed_password.startswith("$2b$"):
            return True  # Not bcrypt

        cost = int(hashed_password.split("$")[2])
        return cost < BCRYPT_ROUNDS
    except Exception:
        return True  # If we can't check, assume it needs updating


def get_password_info(hashed_password: str) -> dict:
    """
    Get information about a password hash (for debugging/admin purposes).

    Args:
        hashed_password: Previously hashed password to analyze

    Returns:
        Dictionary with hash information
    """
    try:
        if hashed_password.startswith("$2b$"):
            cost_str = hashed_password.split("$")[2]
            cost = int(cost_str)
            return {
                "scheme": "bcrypt",
                "cost_factor": cost,
                "meets_minimum": cost >= BCRYPT_ROUNDS,
                "needs_update": cost < BCRYPT_ROUNDS,
                "valid": True
            }
        else:
            return {"scheme": "unknown", "valid": False, "needs_update": True}
    except Exception:
        return {"scheme": "unknown", "valid": False, "needs_update": True}
