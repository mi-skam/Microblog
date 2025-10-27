"""
Integration tests for authentication workflows and session management.

This module tests the complete authentication system including login/logout flows,
session management, JWT cookie handling, CSRF protection, and API authentication
endpoints with realistic scenarios and security validation.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from microblog.auth.models import User
from microblog.auth.password import hash_password
from microblog.server.app import create_app


class TestAuthenticationFlows:
    """Integration tests for authentication workflows."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with authentication setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create content structure
            content_dir = base_dir / "content"
            data_dir = content_dir / "_data"
            templates_dir = content_dir / "templates"

            data_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)

            # Create authentication templates
            self._create_auth_templates(templates_dir)

            # Create test user in database
            db_path = data_dir / "users.db"
            self._create_test_user(db_path)

            # Create config file
            config_data = self._create_test_config(str(base_dir))
            config_file = base_dir / "config.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            yield {
                'base': base_dir,
                'content': content_dir,
                'data': data_dir,
                'templates': templates_dir,
                'config': config_file,
                'db_path': db_path
            }

    def _create_auth_templates(self, templates_dir: Path):
        """Create authentication templates for testing."""
        # Auth directory
        (templates_dir / "auth").mkdir(exist_ok=True)

        # Login template
        login_template = """<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <meta name="csrf-token" content="{{ csrf_token }}">
</head>
<body>
    <h1>Login</h1>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post" action="/auth/login">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div>
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit">Login</button>
    </form>
</body>
</html>"""
        (templates_dir / "auth" / "login.html").write_text(login_template)

        # Logout template
        logout_template = """<!DOCTYPE html>
<html>
<head><title>Logout</title></head>
<body>
    <h1>Logout</h1>
    <p>Are you sure you want to logout?</p>
    <form method="post" action="/auth/logout">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit">Yes, Logout</button>
        <a href="/dashboard">Cancel</a>
    </form>
</body>
</html>"""
        (templates_dir / "auth" / "logout.html").write_text(logout_template)

    def _create_test_user(self, db_path: Path):
        """Create test users with different roles."""
        # Create table first
        User.create_table(db_path)

        # Create admin user
        admin_password_hash = hash_password("admin123")
        User.create_user(
            username="admin",
            email="admin@example.com",
            password_hash=admin_password_hash,
            db_path=db_path
        )

    def _create_test_config(self, base_dir: str) -> dict:
        """Create test configuration for authentication."""
        return {
            'site': {
                'title': 'Auth Test Blog',
                'url': 'https://auth-test.example.com',
                'author': 'Auth Test Author',
                'description': 'Authentication integration test blog'
            },
            'build': {
                'output_dir': f"{base_dir}/build",
                'backup_dir': f"{base_dir}/build.bak",
                'posts_per_page': 5
            },
            'auth': {
                'jwt_secret': 'auth-test-secret-key-that-is-very-long-and-secure-for-testing-purposes',
                'session_expires': 3600
            }
        }

    @pytest.fixture
    def test_client(self, temp_project_dir):
        """Create test client with mocked content directory."""
        import os
        # Set environment variable to point to our test config
        original_config = os.environ.get('MICROBLOG_CONFIG')
        os.environ['MICROBLOG_CONFIG'] = str(temp_project_dir['config'])

        try:
            with patch('microblog.utils.get_content_dir', return_value=temp_project_dir['content']):
                app = create_app(dev_mode=True)
                return TestClient(app)
        finally:
            # Restore original config
            if original_config:
                os.environ['MICROBLOG_CONFIG'] = original_config
            else:
                os.environ.pop('MICROBLOG_CONFIG', None)

    def _extract_csrf_token(self, html_content: str) -> str:
        """Extract CSRF token from HTML content."""
        import re
        patterns = [
            r'name="csrf_token"[^>]*value="([^"]+)"',
            r'content="([^"]+)"[^>]*name="csrf-token"',
            r'name="csrf-token"[^>]*content="([^"]+)"'
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)

        raise ValueError("CSRF token not found in HTML content")

    def test_login_page_display(self, test_client):
        """Test login page displays correctly with CSRF token."""
        response = test_client.get("/auth/login")

        assert response.status_code == 200
        assert "Login" in response.text
        assert 'name="csrf_token"' in response.text
        assert 'name="username"' in response.text
        assert 'name="password"' in response.text
        assert 'action="/auth/login"' in response.text

        # Verify CSRF token is present and extractable
        csrf_token = self._extract_csrf_token(response.text)
        assert csrf_token is not None
        assert len(csrf_token) > 10

    def test_login_with_valid_credentials(self, test_client):
        """Test successful login with valid credentials."""
        # Get login page and extract CSRF token
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        # Submit login form
        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        response = test_client.post("/auth/login", data=login_data, follow_redirects=False)

        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"

        # Should set JWT cookie
        assert "jwt" in response.cookies
        jwt_cookie = response.cookies["jwt"]
        assert jwt_cookie is not None
        assert len(jwt_cookie) > 50  # JWT tokens are long

        # Cookie should have security attributes
        cookie_header = response.headers.get("set-cookie", "")
        assert "HttpOnly" in cookie_header
        assert "Secure" in cookie_header
        assert "SameSite=strict" in cookie_header

    def test_login_with_invalid_username(self, test_client):
        """Test login failure with invalid username."""
        # Get CSRF token
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        # Submit with invalid username
        login_data = {
            "username": "nonexistent",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        response = test_client.post("/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Invalid username or password" in response.text
        assert "jwt" not in response.cookies

    def test_login_with_invalid_password(self, test_client):
        """Test login failure with invalid password."""
        # Get CSRF token
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        # Submit with invalid password
        login_data = {
            "username": "admin",
            "password": "wrongpassword",
            "csrf_token": csrf_token
        }

        response = test_client.post("/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Invalid username or password" in response.text
        assert "jwt" not in response.cookies

    def test_login_with_invalid_csrf_token(self, test_client):
        """Test login failure with invalid CSRF token."""
        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": "invalid-csrf-token"
        }

        response = test_client.post("/auth/login", data=login_data)

        assert response.status_code == 403
        assert "CSRF token validation failed" in response.text

    def test_login_with_missing_csrf_token(self, test_client):
        """Test login failure with missing CSRF token."""
        login_data = {
            "username": "admin",
            "password": "admin123"
            # Missing csrf_token
        }

        response = test_client.post("/auth/login", data=login_data)

        assert response.status_code == 422  # Validation error for missing field

    def test_login_redirect_if_already_authenticated(self, test_client):
        """Test login page redirects if user is already authenticated."""
        # First, authenticate the user
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        login_response = test_client.post("/auth/login", data=login_data, follow_redirects=False)
        assert login_response.status_code == 302

        # Now try to access login page again
        second_login_attempt = test_client.get("/auth/login", follow_redirects=False)
        assert second_login_attempt.status_code == 302
        assert second_login_attempt.headers["location"] == "/dashboard"

    def test_logout_form_display(self, test_client):
        """Test logout form is displayed for authenticated users."""
        # First authenticate
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Access logout page
        logout_response = test_client.get("/auth/logout")

        assert logout_response.status_code == 200
        assert "Logout" in logout_response.text
        assert 'action="/auth/logout"' in logout_response.text
        assert 'name="csrf_token"' in logout_response.text

    def test_logout_redirect_if_not_authenticated(self, test_client):
        """Test logout redirects to login if user is not authenticated."""
        response = test_client.get("/auth/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/auth/login"

    def test_successful_logout(self, test_client):
        """Test successful logout clears JWT cookie."""
        # First authenticate
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Get logout form and CSRF token
        logout_page = test_client.get("/auth/logout")
        logout_csrf_token = self._extract_csrf_token(logout_page.text)

        # Submit logout form
        logout_data = {
            "csrf_token": logout_csrf_token
        }

        logout_response = test_client.post("/auth/logout", data=logout_data, follow_redirects=False)

        # Should redirect to login
        assert logout_response.status_code == 302
        assert logout_response.headers["location"] == "/auth/login"

        # Should clear JWT cookie
        cookie_header = logout_response.headers.get("set-cookie", "")
        assert "jwt=" in cookie_header  # Cookie is being set
        assert "Max-Age=0" in cookie_header  # Cookie is being expired

    def test_logout_with_invalid_csrf_token(self, test_client):
        """Test logout failure with invalid CSRF token."""
        # First authenticate
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Try to logout with invalid CSRF token
        logout_data = {
            "csrf_token": "invalid-token"
        }

        logout_response = test_client.post("/auth/logout", data=logout_data)

        assert logout_response.status_code == 403
        assert "CSRF token validation failed" in logout_response.text

    def test_session_check_api_authenticated(self, test_client):
        """Test session check API for authenticated user."""
        # First authenticate
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Check session
        session_response = test_client.get("/auth/check")

        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["valid"] is True
        assert session_data["user"]["username"] == "admin"
        assert session_data["user"]["role"] == "admin"

    def test_session_check_api_unauthenticated(self, test_client):
        """Test session check API for unauthenticated user."""
        response = test_client.get("/auth/check")

        assert response.status_code == 401
        session_data = response.json()
        assert session_data["valid"] is False

    def test_auth_status_api(self, test_client):
        """Test authentication status API endpoint."""
        # Test unauthenticated status
        unauth_response = test_client.get("/auth/status")
        assert unauth_response.status_code == 200
        unauth_data = unauth_response.json()
        assert unauth_data["authenticated"] is False
        assert unauth_data["user"] is None
        assert unauth_data["cookie_present"] is False

        # Authenticate user
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Test authenticated status
        auth_response = test_client.get("/auth/status")
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert auth_data["authenticated"] is True
        assert auth_data["user"]["username"] == "admin"
        assert auth_data["cookie_present"] is True
        assert auth_data["csrf_token"] is True

    def test_api_login_endpoint(self, test_client):
        """Test JSON API login endpoint."""
        # Get CSRF token first
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        # Test API login
        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        response = test_client.post("/auth/api/login", json=login_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["message"] == "Login successful"
        assert response_data["user"]["username"] == "admin"

        # JWT cookie should be set
        assert "jwt" in response.cookies

    def test_api_login_invalid_credentials(self, test_client):
        """Test API login with invalid credentials."""
        # Get CSRF token
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "wrongpassword",
            "csrf_token": csrf_token
        }

        response = test_client.post("/auth/api/login", json=login_data)

        assert response.status_code == 401
        response_data = response.json()
        assert response_data["success"] is False
        assert "Invalid username or password" in response_data["message"]

    def test_api_logout_endpoint(self, test_client):
        """Test JSON API logout endpoint."""
        # First authenticate
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Get new CSRF token for logout
        status_response = test_client.get("/auth/status")
        # For API logout, we need CSRF token in form data
        logout_data = {
            "csrf_token": csrf_token
        }

        logout_response = test_client.post("/auth/api/logout", data=logout_data)

        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert logout_data["success"] is True
        assert logout_data["message"] == "Logout successful"

        # Cookie should be cleared
        cookie_header = logout_response.headers.get("set-cookie", "")
        assert "Max-Age=0" in cookie_header

    def test_protected_route_access_control(self, test_client):
        """Test that protected routes require authentication."""
        # Try to access dashboard without authentication
        dashboard_response = test_client.get("/dashboard/", follow_redirects=False)
        assert dashboard_response.status_code == 302
        assert dashboard_response.headers["location"] == "/auth/login"

        # Authenticate and try again
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        test_client.post("/auth/login", data=login_data)

        # Now dashboard should be accessible
        dashboard_response = test_client.get("/dashboard/")
        assert dashboard_response.status_code == 200

    def test_jwt_token_expiration_simulation(self, test_client):
        """Test behavior with expired JWT tokens."""
        # Authenticate user
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        login_response = test_client.post("/auth/login", data=login_data)
        jwt_token = login_response.cookies["jwt"]

        # Simulate expired token by setting a malformed/expired JWT
        test_client.cookies.set("jwt", "expired.jwt.token")

        # Try to access protected route
        dashboard_response = test_client.get("/dashboard/", follow_redirects=False)
        assert dashboard_response.status_code == 302
        assert dashboard_response.headers["location"] == "/auth/login"

    def test_csrf_token_consistency(self, test_client):
        """Test CSRF token consistency across requests."""
        # Get first CSRF token
        first_response = test_client.get("/auth/login")
        first_csrf = self._extract_csrf_token(first_response.text)

        # Get second CSRF token in same session
        second_response = test_client.get("/auth/login")
        second_csrf = self._extract_csrf_token(second_response.text)

        # CSRF tokens should be consistent within session
        assert first_csrf == second_csrf

    def test_single_user_authentication(self, test_client):
        """Test authentication with the single admin user account."""
        # Clear any existing authentication
        test_client.cookies.clear()

        # Get fresh login page
        login_page = test_client.get("/auth/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        # Login with admin credentials
        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        login_response = test_client.post("/auth/login", data=login_data, follow_redirects=False)
        assert login_response.status_code == 302
        assert "jwt" in login_response.cookies

        # Verify session is valid for admin user
        session_check = test_client.get("/auth/check")
        assert session_check.status_code == 200
        session_data = session_check.json()
        assert session_data["user"]["username"] == "admin"

    def test_complete_authentication_workflow(self, test_client):
        """Test complete authentication workflow from login to logout."""
        # Step 1: Access login page
        login_page = test_client.get("/auth/login")
        assert login_page.status_code == 200
        csrf_token = self._extract_csrf_token(login_page.text)

        # Step 2: Submit login form
        login_data = {
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token
        }

        login_response = test_client.post("/auth/login", data=login_data, follow_redirects=False)
        assert login_response.status_code == 302
        assert login_response.headers["location"] == "/dashboard"
        assert "jwt" in login_response.cookies

        # Step 3: Access protected route
        dashboard_response = test_client.get("/dashboard/")
        assert dashboard_response.status_code == 200

        # Step 4: Check session status
        session_response = test_client.get("/auth/check")
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["valid"] is True
        assert session_data["user"]["username"] == "admin"

        # Step 5: Access logout form
        logout_page = test_client.get("/auth/logout")
        assert logout_page.status_code == 200
        logout_csrf_token = self._extract_csrf_token(logout_page.text)

        # Step 6: Submit logout form
        logout_data = {
            "csrf_token": logout_csrf_token
        }

        logout_response = test_client.post("/auth/logout", data=logout_data, follow_redirects=False)
        assert logout_response.status_code == 302
        assert logout_response.headers["location"] == "/auth/login"

        # Step 7: Verify session is invalidated
        post_logout_session = test_client.get("/auth/check")
        assert post_logout_session.status_code == 401
        post_logout_data = post_logout_session.json()
        assert post_logout_data["valid"] is False

        # Step 8: Verify protected routes are inaccessible
        post_logout_dashboard = test_client.get("/dashboard/", follow_redirects=False)
        assert post_logout_dashboard.status_code == 302
        assert post_logout_dashboard.headers["location"] == "/auth/login"