"""
Authentication and security middleware for FastAPI microblog application.

This module provides JWT authentication middleware, CSRF protection, and session
management following the security specifications from the auth flow diagram.
"""

import secrets
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from microblog.auth.jwt_handler import verify_jwt_token
from microblog.server.config import get_config


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware that validates tokens from httpOnly cookies.

    Features:
    - Extracts JWT tokens from httpOnly cookies
    - Validates tokens and extracts user claims
    - Adds user context to request state
    - Handles automatic redirects for protected routes
    """

    def __init__(self, app, cookie_name: str = "jwt", protected_paths: list[str] = None):
        super().__init__(app)
        self.cookie_name = cookie_name
        # Default protected paths - can be overridden
        self.protected_paths = protected_paths or [
            "/dashboard",
            "/api/",
            "/admin/"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware."""
        # Extract JWT token from cookie
        token = request.cookies.get(self.cookie_name)

        # Initialize user context
        request.state.user = None
        request.state.authenticated = False

        # Validate token if present
        if token:
            payload = verify_jwt_token(token)
            if payload:
                # Token is valid - set user context
                request.state.user = {
                    "user_id": payload["user_id"],
                    "username": payload["username"],
                    "role": payload.get("role", "admin")
                }
                request.state.authenticated = True

        # Check if route requires authentication
        if self._is_protected_path(request.url.path):
            if not request.state.authenticated:
                # Redirect unauthenticated users to login
                if request.url.path.startswith("/api/"):
                    # Return JSON error for API routes
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={"error": "Authentication required", "valid": False}
                    )
                else:
                    # Redirect to login for web routes
                    return RedirectResponse(
                        url="/auth/login",
                        status_code=status.HTTP_302_FOUND
                    )

        # Process request
        response = await call_next(request)
        return response

    def _is_protected_path(self, path: str) -> bool:
        """Check if the given path requires authentication."""
        return any(path.startswith(protected) for protected in self.protected_paths)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware using synchronizer token pattern.

    Features:
    - Generates CSRF tokens for GET requests
    - Validates CSRF tokens for state-changing operations
    - Stores tokens in secure cookies and validates from forms/headers
    - Exempts safe methods (GET, HEAD, OPTIONS) from validation
    """

    def __init__(
        self,
        app,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        form_field: str = "csrf_token",
        protected_paths: list[str] = None
    ):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.form_field = form_field
        # CSRF protection applies to state-changing operations
        self.protected_paths = protected_paths or [
            "/auth/login",
            "/auth/logout",
            "/api/",
            "/dashboard/"
        ]
        # Safe methods that don't require CSRF validation
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through CSRF protection middleware."""
        # Initialize CSRF context
        request.state.csrf_token = None

        # Get or generate CSRF token
        csrf_token = self._get_or_generate_csrf_token(request)
        request.state.csrf_token = csrf_token

        # Validate CSRF token for state-changing operations
        if (request.method not in self.safe_methods and
            self._is_protected_path(request.url.path)):

            if not self._validate_csrf_token(request):
                # CSRF validation failed
                if request.url.path.startswith("/api/"):
                    # Return JSON error for API routes
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"error": "CSRF token validation failed"}
                    )
                else:
                    # Return error for web routes
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF token validation failed"
                    )

        # Process request
        response = await call_next(request)

        # Set CSRF token cookie if it's a new token
        if not request.cookies.get(self.cookie_name):
            self._set_csrf_cookie(response, csrf_token)

        return response

    def _get_or_generate_csrf_token(self, request: Request) -> str:
        """Get existing CSRF token from cookie or generate a new one."""
        token = request.cookies.get(self.cookie_name)
        if not token:
            token = self._generate_csrf_token()
        return token

    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from request."""
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return False

        # Get token from request (header or form)
        request_token = None

        # Try header first
        if self.header_name in request.headers:
            request_token = request.headers[self.header_name]

        # For form data, we'll need to check the form fields
        # This will be handled by the route handlers since we need to parse the form
        # For now, we'll accept the header validation

        return request_token and secrets.compare_digest(cookie_token, request_token)

    def _set_csrf_cookie(self, response: Response, token: str) -> None:
        """Set CSRF token cookie with secure attributes."""
        config = get_config()

        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=config.auth.session_expires,  # Same as JWT expiration
            httponly=False,  # CSRF tokens need to be accessible to JS
            secure=True,  # HTTPS only
            samesite="strict"  # CSRF protection
        )

    def _is_protected_path(self, path: str) -> bool:
        """Check if the given path requires CSRF protection."""
        return any(path.startswith(protected) for protected in self.protected_paths)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware to add security-related HTTP headers.

    Adds headers like X-Frame-Options, X-Content-Type-Options, etc.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


def get_current_user(request: Request) -> dict[str, Any] | None:
    """
    Helper function to get current authenticated user from request state.

    Args:
        request: FastAPI request object

    Returns:
        User dict if authenticated, None otherwise
    """
    return getattr(request.state, "user", None)


def require_authentication(request: Request) -> dict[str, Any]:
    """
    Helper function that requires authentication and returns user.

    Args:
        request: FastAPI request object

    Returns:
        User dict

    Raises:
        HTTPException: If user is not authenticated
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def get_csrf_token(request: Request) -> str | None:
    """
    Helper function to get CSRF token from request state.

    Args:
        request: FastAPI request object

    Returns:
        CSRF token string if available, None otherwise
    """
    return getattr(request.state, "csrf_token", None)


def validate_csrf_from_form(request: Request, form_data: dict) -> bool:
    """
    Helper function to validate CSRF token from form data.

    Args:
        request: FastAPI request object
        form_data: Parsed form data dictionary

    Returns:
        True if CSRF token is valid, False otherwise
    """
    cookie_token = request.cookies.get("csrf_token")
    form_token = form_data.get("csrf_token")

    if not cookie_token or not form_token:
        return False

    return secrets.compare_digest(cookie_token, form_token)
