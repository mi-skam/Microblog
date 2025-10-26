"""
JWT token generation and validation utilities.

This module provides JWT token creation and validation using the configured
JWT secret and expiration settings from the configuration system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from microblog.server.config import get_config


def create_jwt_token(user_id: int, username: str) -> str:
    """
    Create a JWT token for the authenticated user.

    Args:
        user_id: User ID to include in token
        username: Username to include in token

    Returns:
        Encoded JWT token string

    Raises:
        RuntimeError: If configuration is missing or invalid
    """
    config = get_config()

    if not config.auth.jwt_secret:
        raise RuntimeError("JWT secret not configured")

    # Calculate expiration time
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=config.auth.session_expires)

    # Create token payload
    payload = {
        "user_id": user_id,
        "username": username,
        "role": "admin",  # Fixed role as per ERD specification
        "exp": expires,
        "iat": now
    }

    # Encode token
    try:
        token = jwt.encode(payload, config.auth.jwt_secret, algorithm="HS256")
        return token
    except JWTError as e:
        raise RuntimeError(f"Failed to create JWT token: {e}")


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Dictionary with token payload if valid, None if invalid
    """
    if not token:
        return None

    try:
        config = get_config()

        if not config.auth.jwt_secret:
            return None

        # Decode and verify token
        payload = jwt.decode(token, config.auth.jwt_secret, algorithms=["HS256"])

        # Validate required fields
        required_fields = ["user_id", "username", "exp", "iat"]
        if not all(field in payload for field in required_fields):
            return None

        # Check if token is expired (jose should handle this, but double-check)
        exp_timestamp = payload["exp"]
        if isinstance(exp_timestamp, (int, float)):
            exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                return None

        return payload

    except JWTError:
        return None
    except Exception:
        return None


def decode_jwt_token_unsafe(token: str) -> Optional[dict]:
    """
    Decode JWT token without verification (for debugging/inspection).

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary with token payload if decodable, None otherwise
    """
    if not token:
        return None

    try:
        # Decode without verification
        payload = jwt.get_unverified_claims(token)
        return payload
    except JWTError:
        return None
    except Exception:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a JWT token without full verification.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime if extractable, None otherwise
    """
    payload = decode_jwt_token_unsafe(token)
    if not payload or "exp" not in payload:
        return None

    try:
        exp_timestamp = payload["exp"]
        if isinstance(exp_timestamp, (int, float)):
            return datetime.fromtimestamp(exp_timestamp, timezone.utc)
    except (ValueError, OSError):
        pass

    return None


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired without full verification.

    Args:
        token: JWT token string

    Returns:
        True if token is expired, False if valid or indeterminate
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True  # Assume expired if we can't determine

    return expiry < datetime.now(timezone.utc)


def refresh_token(token: str) -> Optional[str]:
    """
    Create a new token with refreshed expiration if the current token is valid.

    Args:
        token: Current JWT token

    Returns:
        New JWT token if refresh successful, None if current token invalid
    """
    payload = verify_jwt_token(token)
    if not payload:
        return None

    # Create new token with same user info
    try:
        return create_jwt_token(payload["user_id"], payload["username"])
    except RuntimeError:
        return None