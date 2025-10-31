"""
Authentication routes for login, logout, and session management.

This module provides FastAPI routes for user authentication following the
JWT-based authentication flow with secure cookie handling and CSRF protection.
"""

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from microblog.auth.jwt_handler import create_jwt_token
from microblog.auth.models import User
from microblog.auth.password import verify_password
from microblog.server.config import get_config
from microblog.server.middleware import (
    get_csrf_token,
    get_current_user,
    validate_csrf_from_form,
)
from microblog.server.security import InputSanitizer, log_security_event
from microblog.utils import get_content_dir
from microblog.utils.logging import get_security_logger

# Initialize router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Templates will be accessed from app.state.templates


class LoginRequest(BaseModel):
    """Pydantic model for login request validation."""
    username: str
    password: str
    csrf_token: str


class AuthResponse(BaseModel):
    """Pydantic model for authentication responses."""
    success: bool
    message: str
    user: dict | None = None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Display the login page with CSRF token.

    Returns:
        HTML login form with embedded CSRF token
    """
    # Check if user is already authenticated
    if get_current_user(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    # Get CSRF token for the form
    csrf_token = get_csrf_token(request)

    return request.app.state.templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "csrf_token": csrf_token,
            "title": "Login - Microblog"
        }
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    """
    Authenticate user and create session with JWT cookie.

    Args:
        request: FastAPI request object
        response: FastAPI response object
        username: Username from form
        password: Password from form
        csrf_token: CSRF token from form

    Returns:
        Redirect to dashboard on success, error response on failure
    """
    config = get_config()

    # Sanitize input data
    try:
        username = InputSanitizer.sanitize_string(username, max_length=100)
        # Note: password is not sanitized to preserve original characters
    except ValueError as e:
        log_security_event("input_validation_failure", request, {
            "endpoint": "/auth/login",
            "reason": str(e),
            "username": username[:50]  # Log partial username for debugging
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        ) from e

    # Validate CSRF token
    form_data = {"csrf_token": csrf_token}
    if not validate_csrf_from_form(request, form_data):
        log_security_event("csrf_violation", request, {
            "endpoint": "/auth/login",
            "reason": "Invalid CSRF token",
            "username": username
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )

    # Get database path from config
    db_path = get_content_dir() / "_data" / "users.db"

    # Check if user exists in the system
    if not User.user_exists(db_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No admin user configured. Please set up the system first."
        )

    # Authenticate user
    user = User.get_by_username(username, db_path)
    if not user or not verify_password(password, user.password_hash):
        # Log authentication failure for security monitoring
        security_logger = get_security_logger()
        security_logger.auth_failure(
            user_id=username,
            ip_address=request.client.host if request.client else "unknown",
            reason="Invalid credentials"
        )

        log_security_event("auth_failure", request, {
            "endpoint": "/auth/login",
            "username": username,
            "reason": "Invalid credentials"
        })

        # Return error for invalid credentials
        csrf_token = get_csrf_token(request)
        return request.app.state.templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "csrf_token": csrf_token,
                "error": "Invalid username or password",
                "title": "Login - Microblog"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Create JWT token
    try:
        jwt_token = create_jwt_token(user.user_id, user.username)

        # Log successful authentication
        log_security_event("auth_success", request, {
            "endpoint": "/auth/login",
            "username": username,
            "user_id": user.user_id
        })

    except RuntimeError as e:
        log_security_event("auth_error", request, {
            "endpoint": "/auth/login",
            "username": username,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        ) from e

    # Create response and set secure JWT cookie
    redirect_response = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_302_FOUND
    )

    # Set JWT cookie with security attributes
    redirect_response.set_cookie(
        key="jwt",
        value=jwt_token,
        max_age=config.auth.session_expires,
        httponly=True,  # Prevent XSS access
        secure=True,    # HTTPS only
        samesite="strict"  # CSRF protection
    )

    return redirect_response


@router.post("/logout")
async def logout(request: Request, csrf_token: str = Form(...)):
    """
    Logout user by clearing the JWT cookie.

    Args:
        request: FastAPI request object
        csrf_token: CSRF token from form

    Returns:
        Redirect to login page with cleared cookie
    """
    # Validate CSRF token
    form_data = {"csrf_token": csrf_token}
    if not validate_csrf_from_form(request, form_data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )

    # Create response and clear JWT cookie
    redirect_response = RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_302_FOUND
    )

    # Clear JWT cookie by setting it to expire in the past
    redirect_response.set_cookie(
        key="jwt",
        value="",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return redirect_response


@router.get("/check")
async def check_session(request: Request) -> JSONResponse:
    """
    Check if current session is valid (for AJAX/HTMX requests).

    Args:
        request: FastAPI request object

    Returns:
        JSON response with session validity and user info
    """
    user = get_current_user(request)

    if user:
        return JSONResponse(
            content={
                "valid": True,
                "user": {
                    "username": user["username"],
                    "role": user["role"]
                }
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={"valid": False},
            status_code=status.HTTP_401_UNAUTHORIZED
        )


@router.get("/status")
async def auth_status(request: Request) -> JSONResponse:
    """
    Get detailed authentication status (for debugging).

    Args:
        request: FastAPI request object

    Returns:
        JSON response with detailed auth status
    """
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    return JSONResponse(
        content={
            "authenticated": user is not None,
            "user": user,
            "csrf_token": csrf_token is not None,
            "cookie_present": "jwt" in request.cookies
        },
        status_code=status.HTTP_200_OK
    )


@router.api_route("/logout", methods=["GET"])
async def logout_get(request: Request):
    """
    Handle GET requests to logout (redirect to dashboard with logout form).

    This provides a safe way to initiate logout via GET request.
    """
    # If not authenticated, redirect to login
    if not get_current_user(request):
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    # Generate logout form with CSRF token
    csrf_token = get_csrf_token(request)

    return request.app.state.templates.TemplateResponse(
        request,
        "auth/logout.html",
        {
            "csrf_token": csrf_token,
            "title": "Logout - Microblog"
        }
    )


# API endpoints for JSON responses (for HTMX/AJAX)
@router.post("/api/login")
async def api_login(request: Request, login_data: LoginRequest) -> JSONResponse:
    """
    API endpoint for login with JSON response.

    Args:
        request: FastAPI request object
        login_data: Login request data

    Returns:
        JSON response with login result
    """
    config = get_config()

    # Sanitize input data
    try:
        sanitized_username = InputSanitizer.sanitize_string(login_data.username, max_length=100)
    except ValueError as e:
        log_security_event("input_validation_failure", request, {
            "endpoint": "/auth/api/login",
            "reason": str(e),
            "username": login_data.username[:50]
        })
        return JSONResponse(
            content=AuthResponse(
                success=False,
                message="Invalid input data"
            ).model_dump(),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Validate CSRF token
    form_data = {"csrf_token": login_data.csrf_token}
    if not validate_csrf_from_form(request, form_data):
        log_security_event("csrf_violation", request, {
            "endpoint": "/auth/api/login",
            "reason": "Invalid CSRF token",
            "username": sanitized_username
        })
        return JSONResponse(
            content=AuthResponse(
                success=False,
                message="CSRF token validation failed"
            ).model_dump(),
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Get database path
    db_path = get_content_dir() / "_data" / "users.db"

    # Check if user exists
    if not User.user_exists(db_path):
        return JSONResponse(
            content=AuthResponse(
                success=False,
                message="No admin user configured"
            ).model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Authenticate user
    user = User.get_by_username(sanitized_username, db_path)
    if not user or not verify_password(login_data.password, user.password_hash):
        # Log authentication failure
        security_logger = get_security_logger()
        security_logger.auth_failure(
            user_id=sanitized_username,
            ip_address=request.client.host if request.client else "unknown",
            reason="Invalid credentials"
        )

        log_security_event("auth_failure", request, {
            "endpoint": "/auth/api/login",
            "username": sanitized_username,
            "reason": "Invalid credentials"
        })

        return JSONResponse(
            content=AuthResponse(
                success=False,
                message="Invalid username or password"
            ).model_dump(),
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Create JWT token
    try:
        jwt_token = create_jwt_token(user.user_id, user.username)

        # Log successful authentication
        log_security_event("auth_success", request, {
            "endpoint": "/auth/api/login",
            "username": sanitized_username,
            "user_id": user.user_id
        })

    except RuntimeError as e:
        log_security_event("auth_error", request, {
            "endpoint": "/auth/api/login",
            "username": sanitized_username,
            "error": str(e)
        })
        return JSONResponse(
            content=AuthResponse(
                success=False,
                message=f"Failed to create session: {str(e)}"
            ).model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Create response
    response = JSONResponse(
        content=AuthResponse(
            success=True,
            message="Login successful",
            user=user.to_dict()
        ).model_dump(),
        status_code=status.HTTP_200_OK
    )

    # Set JWT cookie
    response.set_cookie(
        key="jwt",
        value=jwt_token,
        max_age=config.auth.session_expires,
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return response


@router.post("/api/logout")
async def api_logout(request: Request, csrf_token: str = Form(...)) -> JSONResponse:
    """
    API endpoint for logout with JSON response.

    Args:
        request: FastAPI request object
        csrf_token: CSRF token from form

    Returns:
        JSON response with logout result
    """
    # Validate CSRF token
    form_data = {"csrf_token": csrf_token}
    if not validate_csrf_from_form(request, form_data):
        return JSONResponse(
            content=AuthResponse(
                success=False,
                message="CSRF token validation failed"
            ).model_dump(),
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Create response
    response = JSONResponse(
        content=AuthResponse(
            success=True,
            message="Logout successful"
        ).model_dump(),
        status_code=status.HTTP_200_OK
    )

    # Clear JWT cookie
    response.set_cookie(
        key="jwt",
        value="",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return response
