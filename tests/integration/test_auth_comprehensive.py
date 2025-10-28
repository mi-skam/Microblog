"""
Comprehensive integration tests for authentication system.

This module provides extensive coverage for the authentication system including
JWT handling, password operations, user models, and middleware integration.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from microblog.auth.jwt_handler import create_jwt_token, verify_jwt_token
from microblog.auth.models import User
from microblog.auth.password import hash_password, verify_password


class TestAuthenticationSystemComprehensive:
    """Comprehensive tests for authentication system components."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_users.db"
            yield db_path

    def test_password_hashing_operations(self):
        """Test password hashing and verification operations."""
        # Test password hashing
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")

        # Test password verification
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
        assert verify_password("", hashed) is False

        # Test with None/empty values
        assert verify_password(password, None) is False
        assert verify_password(None, hashed) is False

    def test_jwt_token_operations(self):
        """Test JWT token creation and verification."""
        with patch('microblog.server.config.get_config') as mock_config:
            # Mock config
            mock_config.return_value.auth.jwt_secret = "test-secret-key-for-jwt-testing"
            mock_config.return_value.auth.session_expires = 3600

            # Test token creation
            user_id = 1
            username = "testuser"
            token = create_jwt_token(user_id, username)

            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

            # Test token verification
            payload = verify_jwt_token(token)
            assert payload is not None
            assert payload["user_id"] == user_id
            assert payload["username"] == username
            assert "exp" in payload
            assert "iat" in payload

            # Test invalid token
            invalid_payload = verify_jwt_token("invalid.token.here")
            assert invalid_payload is None

            # Test None token
            none_payload = verify_jwt_token(None)
            assert none_payload is None

    def test_user_model_operations(self, temp_db_path):
        """Test User model database operations."""
        # Test initial state - no users exist
        assert User.user_exists(temp_db_path) is False

        # Test creating a user
        username = "admin"
        password = "test_password"
        user = User.create_user(username, password, temp_db_path)

        assert user is not None
        assert user.username == username
        assert user.user_id is not None
        assert user.password_hash is not None
        assert user.password_hash != password

        # Test user exists after creation
        assert User.user_exists(temp_db_path) is True

        # Test getting user by username
        retrieved_user = User.get_by_username(username, temp_db_path)
        assert retrieved_user is not None
        assert retrieved_user.username == username
        assert retrieved_user.user_id == user.user_id

        # Test getting non-existent user
        missing_user = User.get_by_username("nonexistent", temp_db_path)
        assert missing_user is None

        # Test user serialization
        user_dict = user.to_dict()
        assert user_dict["username"] == username
        assert user_dict["user_id"] == user.user_id
        assert "password_hash" not in user_dict  # Should not include sensitive data

    def test_middleware_integration(self):
        """Test middleware integration with authentication."""
        from microblog.server.middleware import (
            AuthenticationMiddleware,
            CSRFProtectionMiddleware,
            SecurityHeadersMiddleware,
            get_current_user,
            get_csrf_token,
            validate_csrf_from_form,
        )

        # Create a test app with middleware
        app = FastAPI()

        # Add middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(CSRFProtectionMiddleware)
        app.add_middleware(AuthenticationMiddleware)

        @app.get("/test")
        async def test_endpoint(request):
            return {"message": "test"}

        @app.get("/protected")
        async def protected_endpoint(request):
            user = get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return {"user": user}

        client = TestClient(app)

        # Test unauthenticated request
        response = client.get("/test")
        assert response.status_code == 200

        # Test security headers are added
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers

        # Test protected route without authentication
        response = client.get("/protected")
        assert response.status_code == 302  # Should redirect to login

        # Test with mocked JWT token
        with patch('microblog.auth.jwt_handler.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": 1,
                "username": "admin",
                "role": "admin"
            }

            client.cookies.set("jwt", "test-token")
            response = client.get("/protected")
            assert response.status_code == 200
            assert response.json()["user"]["username"] == "admin"

    def test_csrf_validation_functions(self):
        """Test CSRF validation helper functions."""
        from microblog.server.middleware import validate_csrf_from_form

        # Create mock request with cookies
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": "valid-token"}

        # Test valid CSRF token
        form_data = {"csrf_token": "valid-token"}
        assert validate_csrf_from_form(mock_request, form_data) is True

        # Test invalid CSRF token
        form_data = {"csrf_token": "invalid-token"}
        assert validate_csrf_from_form(mock_request, form_data) is False

        # Test missing form token
        form_data = {}
        assert validate_csrf_from_form(mock_request, form_data) is False

        # Test missing cookie token
        mock_request.cookies = {}
        form_data = {"csrf_token": "any-token"}
        assert validate_csrf_from_form(mock_request, form_data) is False

    def test_authentication_error_scenarios(self, temp_db_path):
        """Test various authentication error scenarios."""
        # Test JWT operations with invalid config
        with patch('microblog.server.config.get_config') as mock_config:
            mock_config.return_value.auth.jwt_secret = ""  # Invalid secret

            try:
                create_jwt_token(1, "admin")
                assert False, "Should have raised an exception"
            except RuntimeError:
                pass  # Expected

        # Test user operations on non-existent database
        non_existent_path = Path("/non/existent/path/users.db")
        assert User.user_exists(non_existent_path) is False
        assert User.get_by_username("admin", non_existent_path) is None

        # Test creating user with invalid data
        try:
            User.create_user("", "password", temp_db_path)
            assert False, "Should have raised an exception"
        except ValueError:
            pass  # Expected

    def test_password_edge_cases(self):
        """Test password hashing edge cases."""
        # Test empty password
        try:
            hash_password("")
            assert False, "Should have raised an exception"
        except ValueError:
            pass  # Expected

        # Test None password
        try:
            hash_password(None)
            assert False, "Should have raised an exception"
        except (ValueError, TypeError):
            pass  # Expected

        # Test very long password
        long_password = "a" * 1000
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True

    def test_jwt_token_expiration_handling(self):
        """Test JWT token expiration scenarios."""
        with patch('microblog.server.config.get_config') as mock_config:
            mock_config.return_value.auth.jwt_secret = "test-secret-key"
            mock_config.return_value.auth.session_expires = -1  # Expired immediately

            # Create token that expires immediately
            token = create_jwt_token(1, "admin")

            # Token should be invalid due to expiration
            import time
            time.sleep(1)
            payload = verify_jwt_token(token)
            assert payload is None  # Should be None due to expiration

    def test_user_model_database_errors(self, temp_db_path):
        """Test User model database error handling."""
        # Create a user first
        User.create_user("admin", "password", temp_db_path)

        # Test duplicate user creation
        try:
            User.create_user("admin", "password2", temp_db_path)
            assert False, "Should have raised an exception for duplicate user"
        except ValueError:
            pass  # Expected

        # Test with corrupted database path (directory instead of file)
        directory_path = temp_db_path.parent / "corrupted_db"
        directory_path.mkdir()

        assert User.user_exists(directory_path) is False
        assert User.get_by_username("admin", directory_path) is None

    def test_authentication_middleware_protected_paths(self):
        """Test authentication middleware path protection logic."""
        from microblog.server.middleware import AuthenticationMiddleware

        # Create middleware instance
        middleware = AuthenticationMiddleware(app=None)

        # Test protected paths
        assert middleware._is_protected_path("/dashboard") is True
        assert middleware._is_protected_path("/dashboard/posts") is True
        assert middleware._is_protected_path("/api/posts") is True
        assert middleware._is_protected_path("/admin/settings") is True

        # Test non-protected paths
        assert middleware._is_protected_path("/auth/login") is False
        assert middleware._is_protected_path("/health") is False
        assert middleware._is_protected_path("/") is False

    def test_csrf_middleware_protected_paths(self):
        """Test CSRF middleware path protection logic."""
        from microblog.server.middleware import CSRFProtectionMiddleware

        # Create middleware instance
        middleware = CSRFProtectionMiddleware(app=None)

        # Test protected paths
        assert middleware._is_protected_path("/auth/login") is True
        assert middleware._is_protected_path("/auth/logout") is True
        assert middleware._is_protected_path("/api/posts") is True
        assert middleware._is_protected_path("/dashboard/api/posts") is True

        # Test non-protected paths for CSRF (GET requests)
        assert middleware._is_protected_path("/health") is False
        assert middleware._is_protected_path("/") is False

    def test_security_headers_middleware(self):
        """Test security headers middleware functionality."""
        from microblog.server.middleware import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Check all security headers are present
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_authentication_helper_functions(self):
        """Test authentication helper functions."""
        from microblog.server.middleware import get_current_user, require_authentication

        # Test get_current_user with authenticated request
        mock_request = Mock()
        mock_request.state.user = {"username": "admin", "user_id": 1}

        user = get_current_user(mock_request)
        assert user is not None
        assert user["username"] == "admin"

        # Test get_current_user with unauthenticated request
        mock_request.state.user = None
        user = get_current_user(mock_request)
        assert user is None

        # Test require_authentication with authenticated user
        mock_request.state.user = {"username": "admin", "user_id": 1}
        user = require_authentication(mock_request)
        assert user["username"] == "admin"

        # Test require_authentication with unauthenticated user
        mock_request.state.user = None
        try:
            require_authentication(mock_request)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401