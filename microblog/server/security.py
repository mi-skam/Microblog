"""
Security hardening module with rate limiting, input sanitization, and vulnerability protection.

This module provides comprehensive security features including:
- Rate limiting middleware to prevent brute force attacks
- Input sanitization utilities for XSS and injection prevention
- Security audit logging integration
- Additional vulnerability protection mechanisms
"""

import re
import time
from collections import defaultdict
from typing import Any
from urllib.parse import unquote

from fastapi import HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from microblog.utils.logging import get_security_logger


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent brute force attacks and API abuse.

    Features:
    - Configurable rate limits per endpoint
    - IP-based rate limiting
    - Customizable time windows and limits
    - Integration with security audit logging
    - Automatic threat detection and logging
    """

    def __init__(
        self,
        app,
        default_rate_limit: str = "100/minute",
        auth_rate_limit: str = "5/minute",
        api_rate_limit: str = "60/minute"
    ):
        super().__init__(app)
        self.security_logger = get_security_logger()

        # Initialize limiter with Redis-like in-memory storage
        self.limiter = Limiter(key_func=get_remote_address)

        # Store rate limit configurations
        self.default_rate_limit = default_rate_limit
        self.auth_rate_limit = auth_rate_limit
        self.api_rate_limit = api_rate_limit

        # In-memory storage for rate limiting (production should use Redis)
        self.request_counts: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "window_start": time.time(),
            "blocked_until": 0
        })

        # Track suspicious activity
        self.suspicious_ips: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "failed_attempts": 0,
            "first_attempt": time.time(),
            "blocked_until": 0
        })

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiting middleware."""
        client_ip = get_remote_address(request)
        path = request.url.path
        method = request.method

        # Determine rate limit based on endpoint
        rate_limit_config = self._get_rate_limit_for_path(path)

        # Check if IP is currently blocked for suspicious activity
        if self._is_ip_blocked(client_ip):
            self.security_logger.suspicious_activity(
                "Blocked IP attempted access",
                {
                    "ip_address": client_ip,
                    "path": path,
                    "method": method,
                    "user_agent": request.headers.get("User-Agent", "Unknown")
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. IP temporarily blocked."
            )

        # Apply rate limiting
        if not self._check_rate_limit(client_ip, path, rate_limit_config):
            # Log rate limit violation
            self.security_logger.suspicious_activity(
                "Rate limit exceeded",
                {
                    "ip_address": client_ip,
                    "path": path,
                    "method": method,
                    "rate_limit": rate_limit_config,
                    "user_agent": request.headers.get("User-Agent", "Unknown")
                }
            )

            # Track suspicious activity for auth endpoints
            if path.startswith("/auth/"):
                self._track_suspicious_activity(client_ip)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        # Process request
        response = await call_next(request)

        # Log auth failures for additional monitoring
        if (path.startswith("/auth/login") and
            response.status_code == status.HTTP_401_UNAUTHORIZED):
            self._track_auth_failure(client_ip, request)

        return response

    def _get_rate_limit_for_path(self, path: str) -> dict[str, int]:
        """Get rate limit configuration for the given path."""
        if path.startswith("/auth/"):
            # Stricter limits for authentication endpoints
            return {"requests": 5, "window": 60}  # 5 requests per minute
        elif path.startswith("/api/"):
            # Moderate limits for API endpoints
            return {"requests": 60, "window": 60}  # 60 requests per minute
        else:
            # Default limits for other endpoints
            return {"requests": 100, "window": 60}  # 100 requests per minute

    def _check_rate_limit(self, client_ip: str, path: str, config: dict[str, int]) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        key = f"{client_ip}:{path}"

        request_data = self.request_counts[key]

        # Reset window if expired
        if current_time - request_data["window_start"] >= config["window"]:
            request_data["count"] = 0
            request_data["window_start"] = current_time

        # Check if limit exceeded
        if request_data["count"] >= config["requests"]:
            return False

        # Increment counter
        request_data["count"] += 1
        return True

    def _track_suspicious_activity(self, client_ip: str):
        """Track suspicious activity and implement progressive blocking."""
        current_time = time.time()
        activity = self.suspicious_ips[client_ip]

        # Reset if window expired (1 hour)
        if current_time - activity["first_attempt"] >= 3600:
            activity["failed_attempts"] = 0
            activity["first_attempt"] = current_time
            activity["blocked_until"] = 0

        activity["failed_attempts"] += 1

        # Progressive blocking: 5 attempts = 5 min, 10 = 30 min, 15+ = 2 hours
        if activity["failed_attempts"] >= 15:
            activity["blocked_until"] = current_time + 7200  # 2 hours
        elif activity["failed_attempts"] >= 10:
            activity["blocked_until"] = current_time + 1800  # 30 minutes
        elif activity["failed_attempts"] >= 5:
            activity["blocked_until"] = current_time + 300   # 5 minutes

    def _track_auth_failure(self, client_ip: str, request: Request):
        """Track authentication failures for security monitoring."""
        self.security_logger.auth_failure(
            user_id=None,
            ip_address=client_ip,
            reason="Invalid credentials"
        )
        self._track_suspicious_activity(client_ip)

    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked."""
        current_time = time.time()
        activity = self.suspicious_ips[client_ip]
        return current_time < activity["blocked_until"]


class InputSanitizer:
    """
    Input sanitization utilities to prevent XSS, injection attacks, and other threats.

    Features:
    - HTML tag stripping and escaping
    - Script injection prevention
    - Path traversal protection
    - SQL injection pattern detection
    - Command injection prevention
    """

    # Patterns for detecting malicious input
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
    ]

    SQL_INJECTION_PATTERNS = [
        re.compile(r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)', re.IGNORECASE),
        re.compile(r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+', re.IGNORECASE),
        re.compile(r'[\'";]\s*(--|#)', re.IGNORECASE),
    ]

    COMMAND_INJECTION_PATTERNS = [
        re.compile(r'[;&|`$(){}\[\]]'),
        re.compile(r'\.\./'),
        re.compile(r'\\\\'),
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input by removing/escaping dangerous content.

        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            ValueError: If input contains dangerous patterns
        """
        if not isinstance(value, str):
            return str(value)

        # Length check
        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")

        # URL decode to catch encoded attacks
        decoded_value = unquote(value)

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if pattern.search(decoded_value):
                raise ValueError("Potentially malicious script content detected")

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(decoded_value):
                raise ValueError("Potentially malicious SQL content detected")

        # Check for command injection patterns
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if pattern.search(decoded_value):
                raise ValueError("Potentially malicious command content detected")

        # Basic HTML escaping for remaining content
        escaped_value = (value
                        .replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
                        .replace('"', '&quot;')
                        .replace("'", '&#x27;'))

        return escaped_value

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Input filename

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename contains dangerous patterns
        """
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        # Remove directory traversal patterns
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Filename contains invalid path characters")

        # Remove special characters that could be dangerous
        sanitized = re.sub(r'[^\w\-_\.]', '', filename)

        # Ensure it's not empty after sanitization
        if not sanitized:
            raise ValueError("Filename is empty after sanitization")

        return sanitized

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate and sanitize email address.

        Args:
            email: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValueError: If email format is invalid
        """
        if not isinstance(email, str):
            raise ValueError("Email must be a string")

        # Basic email pattern validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not email_pattern.match(email):
            raise ValueError("Invalid email format")

        # Check for suspicious patterns
        if any(pattern.search(email) for pattern in cls.XSS_PATTERNS + cls.SQL_INJECTION_PATTERNS):
            raise ValueError("Email contains suspicious patterns")

        return email.lower().strip()

    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """
        Sanitize URL to prevent various attacks.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL

        Raises:
            ValueError: If URL contains dangerous content
        """
        if not isinstance(url, str):
            raise ValueError("URL must be a string")

        # Check for javascript: or data: schemes
        if re.match(r'^(javascript|data|vbscript):', url, re.IGNORECASE):
            raise ValueError("Dangerous URL scheme detected")

        # Only allow http, https, and relative URLs
        if not re.match(r'^(https?://|/)', url, re.IGNORECASE) and not url.startswith('#'):
            raise ValueError("Invalid URL scheme")

        return url


def create_security_response_headers() -> dict[str, str]:
    """
    Create comprehensive security response headers.

    Returns:
        Dictionary of security headers to add to responses
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; font-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()"
    }


def log_security_event(event_type: str, request: Request, details: dict[str, Any] | None = None):
    """
    Log security-related events with standardized format.

    Args:
        event_type: Type of security event
        request: FastAPI request object
        details: Additional event details
    """
    security_logger = get_security_logger()

    event_data = {
        "ip_address": get_remote_address(request),
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "path": request.url.path,
        "method": request.method,
        "event_type": event_type
    }

    if details:
        event_data.update(details)

    if event_type in ["auth_failure", "csrf_violation", "rate_limit_exceeded"]:
        security_logger.suspicious_activity(f"Security event: {event_type}", event_data)
    else:
        security_logger.logger.info(f"Security event: {event_type}", extra=event_data)


def validate_request_data(data: dict[str, Any], max_fields: int = 50) -> dict[str, Any]:
    """
    Validate and sanitize request data.

    Args:
        data: Request data to validate
        max_fields: Maximum number of fields allowed

    Returns:
        Sanitized request data

    Raises:
        ValueError: If data contains suspicious content
    """
    if len(data) > max_fields:
        raise ValueError(f"Too many fields in request (max: {max_fields})")

    sanitized_data = {}

    for key, value in data.items():
        # Sanitize field name
        if not re.match(r'^[a-zA-Z0-9_-]+$', key):
            raise ValueError(f"Invalid field name: {key}")

        # Sanitize field value
        if isinstance(value, str):
            sanitized_data[key] = InputSanitizer.sanitize_string(value)
        elif isinstance(value, (int, float, bool)):
            sanitized_data[key] = value
        elif value is None:
            sanitized_data[key] = None
        else:
            # Convert other types to string and sanitize
            sanitized_data[key] = InputSanitizer.sanitize_string(str(value))

    return sanitized_data
