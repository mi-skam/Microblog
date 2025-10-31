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
from microblog.server.health import get_health_status, get_simple_health_status
from microblog.server.middleware import (
    AuthenticationMiddleware,
    CSRFProtectionMiddleware,
    SecurityHeadersMiddleware,
)
from microblog.server.routes import api, auth, dashboard
from microblog.utils import get_content_dir
from microblog.utils.logging import setup_logging
from microblog.utils.monitoring import (
    get_monitoring_summary,
    start_monitoring_background_tasks,
)

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

    # Set up logging based on configuration
    setup_logging(
        log_level=config.logging.level,
        log_file=config.logging.file_path,
        max_bytes=config.logging.max_file_size_mb * 1024 * 1024,
        backup_count=config.logging.backup_count,
        console_output=config.logging.console_output
    )

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
    app.include_router(dashboard.router)
    app.include_router(api.router)

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

        # Start monitoring background tasks if enabled
        if config.monitoring.enabled:
            await start_monitoring_background_tasks()
            logger.info("Monitoring background tasks started")

        # Log configuration summary
        logger.info(f"Server configuration: {config.server.host}:{config.server.port}")
        logger.info(f"Site title: {config.site.title}")
        logger.info(f"Development mode: {dev_mode}")
        logger.info(f"Logging level: {config.logging.level}")
        logger.info(f"Monitoring enabled: {config.monitoring.enabled}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown tasks."""
        logger.info("Microblog application shutting down")

        # Stop configuration file watcher
        if dev_mode:
            await config_manager.stop_watcher()
            logger.info("Configuration file watcher stopped")

    # Add comprehensive health check endpoints
    @app.get("/health")
    async def health_check():
        """Comprehensive health check endpoint for monitoring."""
        return await get_health_status()

    @app.get("/health/simple")
    async def simple_health_check():
        """Simple health check endpoint for basic monitoring."""
        return await get_simple_health_status()

    @app.get("/metrics")
    async def metrics_endpoint():
        """Metrics endpoint for monitoring and alerting."""
        return get_monitoring_summary()

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
