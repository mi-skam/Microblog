"""
FastAPI application setup with middleware configuration and route registration.

This module provides the application factory pattern for creating FastAPI instances
with proper middleware layering, security headers, CORS configuration, and route registration.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from microblog.server.config import get_config_manager
from microblog.server.middleware import (
    AuthenticationMiddleware,
    CSRFProtectionMiddleware,
    SecurityHeadersMiddleware,
)
from microblog.server.routes import auth
from microblog.utils import get_content_dir

logger = logging.getLogger(__name__)


def create_app(dev_mode: bool = False) -> FastAPI:
    """
    Create and configure FastAPI application with middleware and routes.

    This factory function creates a FastAPI application instance with:
    - Security headers middleware
    - CSRF protection middleware
    - JWT authentication middleware
    - CORS configuration
    - Route registration
    - Static file serving
    - Template configuration

    Args:
        dev_mode: Enable development mode with hot-reload and debug features

    Returns:
        Configured FastAPI application instance
    """
    # Initialize configuration manager for this app instance
    config_manager = get_config_manager(dev_mode=dev_mode)
    config = config_manager.config

    # Create FastAPI app instance
    app = FastAPI(
        title="Microblog",
        description="A minimal blog application with HTMX-enhanced dashboard",
        version="1.0.0",
        debug=dev_mode,
        docs_url="/api/docs" if dev_mode else None,
        redoc_url="/api/redoc" if dev_mode else None,
    )

    # Configure CORS middleware (must be added first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if dev_mode else [config.site.url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-CSRF-Token"],
    )

    # Add security headers middleware (layer 1 - outermost)
    app.add_middleware(SecurityHeadersMiddleware)

    # Add CSRF protection middleware (layer 2 - before auth)
    app.add_middleware(
        CSRFProtectionMiddleware,
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        form_field="csrf_token",
        protected_paths=[
            "/auth/login",
            "/auth/logout",
            "/api/",
            "/dashboard/"
        ]
    )

    # Add authentication middleware (layer 3 - innermost)
    app.add_middleware(
        AuthenticationMiddleware,
        cookie_name="jwt",
        protected_paths=[
            "/dashboard",
            "/api/",
            "/admin/"
        ]
    )

    # Register route modules
    app.include_router(auth.router)

    # Set up static file serving
    content_dir = get_content_dir()
    static_dir = content_dir / "static"

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Mounted static files from {static_dir}")

    # Set up templates
    template_dir = content_dir / "templates"
    if template_dir.exists():
        # Store templates instance for route handlers
        app.state.templates = Jinja2Templates(directory=str(template_dir))
        logger.info(f"Configured templates from {template_dir}")

    # Add startup event handlers
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup tasks."""
        logger.info("Microblog application starting up")

        # Start configuration file watcher in development mode
        if dev_mode:
            await config_manager.start_watcher()
            logger.info("Configuration hot-reload enabled")

        # Log configuration summary
        logger.info(f"Server configuration: {config.server.host}:{config.server.port}")
        logger.info(f"Site title: {config.site.title}")
        logger.info(f"Development mode: {dev_mode}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown tasks."""
        logger.info("Microblog application shutting down")

        # Stop configuration file watcher
        if dev_mode:
            await config_manager.stop_watcher()
            logger.info("Configuration file watcher stopped")

    # Add basic health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": "microblog",
            "version": "1.0.0"
        }

    # Add root redirect
    @app.get("/")
    async def root():
        """Redirect root to dashboard or login."""
        # This will be handled by the authentication middleware
        # If authenticated, user can access dashboard; if not, they'll be redirected to login
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard")

    logger.info("FastAPI application created and configured successfully")
    return app


def get_app() -> FastAPI:
    """
    Get application instance for production deployment.

    Returns:
        Production-configured FastAPI application
    """
    return create_app(dev_mode=False)


def get_dev_app() -> FastAPI:
    """
    Get application instance for development.

    Returns:
        Development-configured FastAPI application with hot-reload
    """
    return create_app(dev_mode=True)


# Application instance for ASGI servers
app = get_app()
