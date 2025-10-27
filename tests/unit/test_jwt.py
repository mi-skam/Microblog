"""
Comprehensive unit tests for JWT token management.

Tests cover:
- JWT token creation and validation
- Token expiration and refresh
- Configuration integration
- Security edge cases and error handling
- Token utility functions
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from jose import JWTError, jwt

from microblog.auth.jwt_handler import (
    create_jwt_token,
    decode_jwt_token_unsafe,
    get_token_expiry,
    is_token_expired,
    refresh_token,
    verify_jwt_token,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock()
    config.auth.jwt_secret = "test-secret-key-that-is-long-enough-for-testing-purposes"
    config.auth.session_expires = 3600  # 1 hour
    return config


@pytest.fixture
def short_session_config():
    """Create a mock configuration with short session expiry."""
    config = Mock()
    config.auth.jwt_secret = "test-secret-key-that-is-long-enough-for-testing-purposes"
    config.auth.session_expires = 1  # 1 second for expiry testing
    return config


@pytest.fixture
def invalid_config():
    """Create a mock configuration with missing JWT secret."""
    config = Mock()
    config.auth.jwt_secret = None
    config.auth.session_expires = 3600
    return config


class TestCreateJWTToken:
    """Test JWT token creation functionality."""

    @patch('microblog.auth.jwt_handler.get_config')
    def test_create_jwt_token_success(self, mock_get_config, mock_config):
        """Test successful JWT token creation."""
        mock_get_config.return_value = mock_config

        token = create_jwt_token(user_id=1, username="admin")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically quite long

        # Verify token can be decoded
        payload = jwt.decode(token, mock_config.auth.jwt_secret, algorithms=["HS256"])
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    @patch('microblog.auth.jwt_handler.get_config')
    def test_create_jwt_token_no_secret(self, mock_get_config, invalid_config):
        """Test JWT token creation without secret."""
        mock_get_config.return_value = invalid_config

        with pytest.raises(RuntimeError, match="JWT secret not configured"):
            create_jwt_token(user_id=1, username="admin")

    @patch('microblog.auth.jwt_handler.get_config')
    def test_create_jwt_token_empty_secret(self, mock_get_config):
        """Test JWT token creation with empty secret."""
        config = Mock()
        config.auth.jwt_secret = ""
        config.auth.session_expires = 3600
        mock_get_config.return_value = config

        with pytest.raises(RuntimeError, match="JWT secret not configured"):
            create_jwt_token(user_id=1, username="admin")

    @patch('microblog.auth.jwt_handler.get_config')
    def test_create_jwt_token_expiration(self, mock_get_config, mock_config):
        """Test JWT token expiration time calculation."""
        mock_get_config.return_value = mock_config

        before_creation = datetime.now(timezone.utc)
        token = create_jwt_token(user_id=1, username="admin")
        after_creation = datetime.now(timezone.utc)

        payload = jwt.decode(token, mock_config.auth.jwt_secret, algorithms=["HS256"])

        # Verify issued at time - allow for small timing differences
        iat = datetime.fromtimestamp(payload["iat"], timezone.utc)
        time_diff = (after_creation - before_creation).total_seconds()
        assert (iat - before_creation).total_seconds() >= -0.1  # Allow small negative difference
        assert (iat - after_creation).total_seconds() <= 0.1   # Allow small positive difference

        # Verify expiration time
        exp = datetime.fromtimestamp(payload["exp"], timezone.utc)
        expected_exp = iat + timedelta(seconds=mock_config.auth.session_expires)
        assert abs((exp - expected_exp).total_seconds()) < 1

    @patch('microblog.auth.jwt_handler.get_config')
    def test_create_jwt_token_different_users(self, mock_get_config, mock_config):
        """Test JWT token creation for different users."""
        mock_get_config.return_value = mock_config

        token1 = create_jwt_token(user_id=1, username="admin1")
        token2 = create_jwt_token(user_id=2, username="admin2")

        assert token1 != token2

        payload1 = jwt.decode(token1, mock_config.auth.jwt_secret, algorithms=["HS256"])
        payload2 = jwt.decode(token2, mock_config.auth.jwt_secret, algorithms=["HS256"])

        assert payload1["user_id"] == 1
        assert payload1["username"] == "admin1"
        assert payload2["user_id"] == 2
        assert payload2["username"] == "admin2"

    @patch('microblog.auth.jwt_handler.get_config')
    @patch('microblog.auth.jwt_handler.jwt.encode')
    def test_create_jwt_token_encoding_error(self, mock_encode, mock_get_config, mock_config):
        """Test JWT token creation with encoding error."""
        mock_get_config.return_value = mock_config
        mock_encode.side_effect = JWTError("Encoding failed")

        with pytest.raises(RuntimeError, match="Failed to create JWT token"):
            create_jwt_token(user_id=1, username="admin")


class TestVerifyJWTToken:
    """Test JWT token verification functionality."""

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_valid(self, mock_get_config, mock_config):
        """Test verification of valid JWT token."""
        mock_get_config.return_value = mock_config

        # Create a token first
        with patch('microblog.auth.jwt_handler.get_config', return_value=mock_config):
            token = create_jwt_token(user_id=1, username="admin")

        # Verify the token
        payload = verify_jwt_token(token)

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_empty(self, mock_get_config, mock_config):
        """Test verification of empty token."""
        mock_get_config.return_value = mock_config

        payload = verify_jwt_token("")
        assert payload is None

        payload = verify_jwt_token(None)
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_no_secret(self, mock_get_config, invalid_config):
        """Test verification without secret."""
        mock_get_config.return_value = invalid_config

        payload = verify_jwt_token("some.jwt.token")
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_invalid_format(self, mock_get_config, mock_config):
        """Test verification of malformed token."""
        mock_get_config.return_value = mock_config

        payload = verify_jwt_token("invalid.token.format")
        assert payload is None

        payload = verify_jwt_token("not-a-jwt-token")
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_wrong_secret(self, mock_get_config, mock_config):
        """Test verification with wrong secret."""
        # Create token with one secret
        with patch('microblog.auth.jwt_handler.get_config', return_value=mock_config):
            token = create_jwt_token(user_id=1, username="admin")

        # Try to verify with different secret
        wrong_config = Mock()
        wrong_config.auth.jwt_secret = "different-secret-key"
        wrong_config.auth.session_expires = 3600
        mock_get_config.return_value = wrong_config

        payload = verify_jwt_token(token)
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_expired(self, mock_get_config, short_session_config):
        """Test verification of expired token."""
        mock_get_config.return_value = short_session_config

        # Create a token with 1-second expiry
        token = create_jwt_token(user_id=1, username="admin")

        # Wait for expiration
        time.sleep(2)

        # Verify expired token
        payload = verify_jwt_token(token)
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_missing_fields(self, mock_get_config, mock_config):
        """Test verification of token with missing required fields."""
        mock_get_config.return_value = mock_config

        # Create token manually with missing fields
        incomplete_payload = {
            "user_id": 1,
            # Missing username, exp, iat
        }
        token = jwt.encode(incomplete_payload, mock_config.auth.jwt_secret, algorithm="HS256")

        payload = verify_jwt_token(token)
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_verify_jwt_token_manual_expiry_check(self, mock_get_config, mock_config):
        """Test manual expiry check in verification."""
        mock_get_config.return_value = mock_config

        # Create token manually with past expiration
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=1)

        expired_payload = {
            "user_id": 1,
            "username": "admin",
            "role": "admin",
            "exp": past_time.timestamp(),
            "iat": (past_time - timedelta(hours=1)).timestamp()
        }

        token = jwt.encode(expired_payload, mock_config.auth.jwt_secret, algorithm="HS256")

        payload = verify_jwt_token(token)
        assert payload is None


class TestTokenUtilities:
    """Test JWT token utility functions."""

    @patch('microblog.auth.jwt_handler.get_config')
    def test_decode_jwt_token_unsafe_valid(self, mock_get_config, mock_config):
        """Test unsafe token decoding with valid token."""
        mock_get_config.return_value = mock_config

        token = create_jwt_token(user_id=1, username="admin")
        payload = decode_jwt_token_unsafe(token)

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"

    def test_decode_jwt_token_unsafe_empty(self):
        """Test unsafe token decoding with empty token."""
        payload = decode_jwt_token_unsafe("")
        assert payload is None

        payload = decode_jwt_token_unsafe(None)
        assert payload is None

    def test_decode_jwt_token_unsafe_invalid(self):
        """Test unsafe token decoding with invalid token."""
        payload = decode_jwt_token_unsafe("invalid.token")
        assert payload is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_get_token_expiry_valid(self, mock_get_config, mock_config):
        """Test getting token expiry from valid token."""
        mock_get_config.return_value = mock_config

        before_creation = datetime.now(timezone.utc)
        token = create_jwt_token(user_id=1, username="admin")

        expiry = get_token_expiry(token)

        assert expiry is not None
        assert isinstance(expiry, datetime)
        expected_expiry = before_creation + timedelta(seconds=mock_config.auth.session_expires)
        assert abs((expiry - expected_expiry).total_seconds()) < 10  # Allow small timing differences

    def test_get_token_expiry_empty(self):
        """Test getting token expiry from empty token."""
        expiry = get_token_expiry("")
        assert expiry is None

        expiry = get_token_expiry(None)
        assert expiry is None

    def test_get_token_expiry_no_exp_field(self):
        """Test getting token expiry from token without exp field."""
        # Create token manually without exp field
        payload = {"user_id": 1, "username": "admin"}
        secret = "test-secret"
        token = jwt.encode(payload, secret, algorithm="HS256")

        expiry = get_token_expiry(token)
        assert expiry is None

    def test_get_token_expiry_invalid_exp_type(self):
        """Test getting token expiry with invalid exp type."""
        # Create token manually with invalid exp field
        payload = {"user_id": 1, "username": "admin", "exp": "not-a-number"}
        secret = "test-secret"
        token = jwt.encode(payload, secret, algorithm="HS256")

        expiry = get_token_expiry(token)
        assert expiry is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_is_token_expired_valid_token(self, mock_get_config, mock_config):
        """Test checking if valid token is expired."""
        mock_get_config.return_value = mock_config

        token = create_jwt_token(user_id=1, username="admin")

        assert is_token_expired(token) is False

    @patch('microblog.auth.jwt_handler.get_config')
    def test_is_token_expired_expired_token(self, mock_get_config, short_session_config):
        """Test checking if expired token is expired."""
        mock_get_config.return_value = short_session_config

        token = create_jwt_token(user_id=1, username="admin")
        time.sleep(2)  # Wait for expiration

        assert is_token_expired(token) is True

    def test_is_token_expired_invalid_token(self):
        """Test checking if invalid token is expired."""
        assert is_token_expired("invalid.token") is True
        assert is_token_expired("") is True
        assert is_token_expired(None) is True

    @patch('microblog.auth.jwt_handler.get_config')
    def test_refresh_token_valid(self, mock_get_config, mock_config):
        """Test refreshing valid token."""
        mock_get_config.return_value = mock_config

        original_token = create_jwt_token(user_id=1, username="admin")
        refreshed_token = refresh_token(original_token)

        assert refreshed_token is not None
        assert refreshed_token != original_token

        # Verify refreshed token has same user info
        original_payload = verify_jwt_token(original_token)
        refreshed_payload = verify_jwt_token(refreshed_token)

        assert original_payload["user_id"] == refreshed_payload["user_id"]
        assert original_payload["username"] == refreshed_payload["username"]
        assert original_payload["role"] == refreshed_payload["role"]

        # Verify refreshed token has newer expiry
        assert refreshed_payload["exp"] > original_payload["exp"]

    @patch('microblog.auth.jwt_handler.get_config')
    def test_refresh_token_invalid(self, mock_get_config, mock_config):
        """Test refreshing invalid token."""
        mock_get_config.return_value = mock_config

        refreshed_token = refresh_token("invalid.token")
        assert refreshed_token is None

        refreshed_token = refresh_token("")
        assert refreshed_token is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_refresh_token_expired(self, mock_get_config, short_session_config):
        """Test refreshing expired token."""
        mock_get_config.return_value = short_session_config

        token = create_jwt_token(user_id=1, username="admin")
        time.sleep(2)  # Wait for expiration

        refreshed_token = refresh_token(token)
        assert refreshed_token is None

    @patch('microblog.auth.jwt_handler.get_config')
    def test_refresh_token_config_error(self, mock_get_config, mock_config):
        """Test refreshing token with configuration error."""
        # Create valid token first
        token = create_jwt_token(user_id=1, username="admin")

        # Change config to cause error during refresh
        invalid_config = Mock()
        invalid_config.auth.jwt_secret = None
        mock_get_config.return_value = invalid_config

        refreshed_token = refresh_token(token)
        assert refreshed_token is None


class TestJWTIntegration:
    """Test JWT integration scenarios."""

    @patch('microblog.auth.jwt_handler.get_config')
    def test_full_token_lifecycle(self, mock_get_config, mock_config):
        """Test complete token lifecycle: create, verify, refresh."""
        mock_get_config.return_value = mock_config

        # Create token
        original_token = create_jwt_token(user_id=1, username="admin")
        assert original_token is not None

        # Verify token
        payload = verify_jwt_token(original_token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"

        # Refresh token
        refreshed_token = refresh_token(original_token)
        assert refreshed_token is not None
        assert refreshed_token != original_token

        # Verify refreshed token
        refreshed_payload = verify_jwt_token(refreshed_token)
        assert refreshed_payload is not None
        assert refreshed_payload["user_id"] == 1
        assert refreshed_payload["username"] == "admin"

    @patch('microblog.auth.jwt_handler.get_config')
    def test_token_security_headers(self, mock_get_config, mock_config):
        """Test token contains required security information."""
        mock_get_config.return_value = mock_config

        token = create_jwt_token(user_id=1, username="admin")
        payload = verify_jwt_token(token)

        # Verify required security fields
        assert "user_id" in payload
        assert "username" in payload
        assert "role" in payload
        assert "exp" in payload
        assert "iat" in payload

        # Verify role is fixed to admin
        assert payload["role"] == "admin"

        # Verify timestamps are reasonable
        now = datetime.now(timezone.utc).timestamp()
        assert payload["iat"] <= now <= payload["iat"] + 10
        assert payload["exp"] > payload["iat"]