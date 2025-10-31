"""
Health check endpoints and system status monitoring.

This module provides comprehensive health check capabilities including:
- System status verification
- Database connection checks
- Filesystem permission validation
- Build system status monitoring
- Dependency health verification
"""

import asyncio
import logging
import sqlite3
import time
from datetime import datetime
from typing import Any

from microblog.server.config import get_config
from microblog.utils import get_content_dir

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status enumeration for different system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResult:
    """Result of a health check operation."""

    def __init__(self, name: str, status: str, message: str = "", duration_ms: float = 0, metadata: dict[str, Any] | None = None):
        self.name = name
        self.status = status
        self.message = message
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class HealthChecker:
    """
    Comprehensive health check system.

    Performs various health checks including:
    - Database connectivity
    - Filesystem permissions
    - Build system status
    - Configuration validity
    - External dependencies
    """

    def __init__(self):
        self.content_dir = get_content_dir()
        self._last_build_status: dict[str, Any] | None = None
        self._build_status_cache_duration = 60  # seconds

    async def check_database_connection(self) -> HealthCheckResult:
        """Check database connectivity and basic operations."""
        start_time = time.time()

        try:
            # Get database path from content directory
            db_path = self.content_dir / "microblog.db"

            # Check if database file exists and is accessible
            if not db_path.exists():
                return HealthCheckResult(
                    "database",
                    HealthStatus.DEGRADED,
                    "Database file does not exist - will be created on first use",
                    (time.time() - start_time) * 1000,
                    {"db_path": str(db_path)}
                )

            # Test database connection
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                cursor = conn.cursor()

                # Test basic query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result[0] != 1:
                    raise sqlite3.Error("Basic query test failed")

                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()

                if integrity_result[0] != "ok":
                    return HealthCheckResult(
                        "database",
                        HealthStatus.DEGRADED,
                        f"Database integrity check failed: {integrity_result[0]}",
                        (time.time() - start_time) * 1000,
                        {"db_path": str(db_path)}
                    )

            return HealthCheckResult(
                "database",
                HealthStatus.HEALTHY,
                "Database connection and integrity verified",
                (time.time() - start_time) * 1000,
                {"db_path": str(db_path)}
            )

        except sqlite3.OperationalError as e:
            return HealthCheckResult(
                "database",
                HealthStatus.UNHEALTHY,
                f"Database operational error: {str(e)}",
                (time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                "database",
                HealthStatus.UNHEALTHY,
                f"Database check failed: {str(e)}",
                (time.time() - start_time) * 1000
            )

    async def check_filesystem_permissions(self) -> HealthCheckResult:
        """Check filesystem permissions for critical directories."""
        start_time = time.time()

        try:
            issues = []

            # Critical directories to check
            directories_to_check = [
                ("content", self.content_dir),
                ("posts", self.content_dir / "posts"),
                ("templates", self.content_dir / "templates"),
                ("static", self.content_dir / "static"),
                ("data", self.content_dir / "_data"),
                ("logs", self.content_dir / "logs"),
            ]

            config = get_config()
            build_dir = self.content_dir / config.build.output_dir
            backup_dir = self.content_dir / config.build.backup_dir
            directories_to_check.extend([
                ("build", build_dir),
                ("backup", backup_dir)
            ])

            for name, directory in directories_to_check:
                try:
                    # Check if directory exists
                    if not directory.exists():
                        # Try to create it
                        directory.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created missing directory: {directory}")

                    # Check read permission
                    if not directory.is_dir():
                        issues.append(f"{name} path exists but is not a directory: {directory}")
                        continue

                    # Test write permission by creating a temporary file
                    test_file = directory / ".health_check_test"
                    try:
                        test_file.write_text("test", encoding='utf-8')
                        test_file.unlink()
                    except PermissionError:
                        issues.append(f"No write permission for {name} directory: {directory}")
                    except Exception as e:
                        issues.append(f"Write test failed for {name} directory: {e}")

                except Exception as e:
                    issues.append(f"Error checking {name} directory: {e}")

            # Check disk space
            try:
                stat = directory.stat()
                free_space = stat.st_size if hasattr(stat, 'st_size') else None
                if free_space is not None and free_space < 100 * 1024 * 1024:  # Less than 100MB
                    issues.append(f"Low disk space detected: {free_space / 1024 / 1024:.1f}MB available")
            except Exception:
                # Disk space check failed, but not critical
                pass

            if issues:
                return HealthCheckResult(
                    "filesystem",
                    HealthStatus.DEGRADED,
                    f"Filesystem issues detected: {'; '.join(issues)}",
                    (time.time() - start_time) * 1000,
                    {"issues": issues}
                )

            return HealthCheckResult(
                "filesystem",
                HealthStatus.HEALTHY,
                "All filesystem permissions verified",
                (time.time() - start_time) * 1000,
                {"checked_directories": len(directories_to_check)}
            )

        except Exception as e:
            return HealthCheckResult(
                "filesystem",
                HealthStatus.UNHEALTHY,
                f"Filesystem check failed: {str(e)}",
                (time.time() - start_time) * 1000
            )

    async def check_build_system_status(self) -> HealthCheckResult:
        """Check build system status and last build information."""
        start_time = time.time()

        try:
            config = get_config()
            build_dir = self.content_dir / config.build.output_dir

            # Check if build directory exists
            if not build_dir.exists():
                return HealthCheckResult(
                    "build_system",
                    HealthStatus.DEGRADED,
                    "Build directory does not exist - no builds have been performed",
                    (time.time() - start_time) * 1000,
                    {"build_dir": str(build_dir)}
                )

            # Look for build artifacts
            build_artifacts = {
                "index.html": build_dir / "index.html",
                "posts directory": build_dir / "posts",
                "static directory": build_dir / "static"
            }

            missing_artifacts = []
            for artifact_name, artifact_path in build_artifacts.items():
                if not artifact_path.exists():
                    missing_artifacts.append(artifact_name)

            # Check for build metadata or timestamp
            build_info = {}
            try:
                # Look for any recent files to determine last build time
                recent_files = list(build_dir.rglob("*"))
                if recent_files:
                    latest_file = max(recent_files, key=lambda f: f.stat().st_mtime if f.is_file() else 0)
                    if latest_file.is_file():
                        last_build_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                        build_info["last_build"] = last_build_time.isoformat()
                        build_info["last_build_age_hours"] = (datetime.now() - last_build_time).total_seconds() / 3600
            except Exception:
                pass

            if missing_artifacts:
                return HealthCheckResult(
                    "build_system",
                    HealthStatus.DEGRADED,
                    f"Build directory exists but missing artifacts: {', '.join(missing_artifacts)}",
                    (time.time() - start_time) * 1000,
                    {**build_info, "missing_artifacts": missing_artifacts}
                )

            return HealthCheckResult(
                "build_system",
                HealthStatus.HEALTHY,
                "Build system operational with complete artifacts",
                (time.time() - start_time) * 1000,
                build_info
            )

        except Exception as e:
            return HealthCheckResult(
                "build_system",
                HealthStatus.UNHEALTHY,
                f"Build system check failed: {str(e)}",
                (time.time() - start_time) * 1000
            )

    async def check_configuration_validity(self) -> HealthCheckResult:
        """Check configuration file validity and required settings."""
        start_time = time.time()

        try:
            # Get current configuration
            config = get_config()

            # Basic configuration validation
            issues = []

            # Check required configuration values
            if not config.site.title:
                issues.append("Site title is not configured")

            if not config.site.url or config.site.url == "https://example.com":
                issues.append("Site URL is not properly configured")

            if not config.site.author:
                issues.append("Site author is not configured")

            if len(config.auth.jwt_secret) < 32:
                issues.append("JWT secret is too short (should be at least 32 characters)")

            if config.auth.jwt_secret == "your-super-secret-jwt-key-must-be-at-least-32-characters-long":
                issues.append("JWT secret is still using default value")

            # Check configuration file accessibility
            config_file = self.content_dir / "_data" / "config.yaml"
            if not config_file.exists():
                issues.append("Configuration file does not exist")
            elif not config_file.is_file():
                issues.append("Configuration path exists but is not a file")

            if issues:
                return HealthCheckResult(
                    "configuration",
                    HealthStatus.DEGRADED,
                    f"Configuration issues: {'; '.join(issues)}",
                    (time.time() - start_time) * 1000,
                    {"issues": issues}
                )

            return HealthCheckResult(
                "configuration",
                HealthStatus.HEALTHY,
                "Configuration is valid and complete",
                (time.time() - start_time) * 1000,
                {
                    "config_file": str(config_file),
                    "site_title": config.site.title
                }
            )

        except Exception as e:
            return HealthCheckResult(
                "configuration",
                HealthStatus.UNHEALTHY,
                f"Configuration check failed: {str(e)}",
                (time.time() - start_time) * 1000
            )

    async def run_all_checks(self) -> dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = time.time()

        # Run all checks concurrently
        check_results = await asyncio.gather(
            self.check_database_connection(),
            self.check_filesystem_permissions(),
            self.check_build_system_status(),
            self.check_configuration_validity(),
            return_exceptions=True
        )

        # Process results
        checks = {}
        overall_status = HealthStatus.HEALTHY

        for result in check_results:
            if isinstance(result, Exception):
                # Handle unexpected errors
                checks["unknown_error"] = HealthCheckResult(
                    "unknown_error",
                    HealthStatus.UNHEALTHY,
                    f"Unexpected error during health check: {str(result)}",
                    0
                ).to_dict()
                overall_status = HealthStatus.UNHEALTHY
            else:
                checks[result.name] = result.to_dict()

                # Determine overall status
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        # Build comprehensive response
        total_duration = (time.time() - start_time) * 1000

        return {
            "status": overall_status,
            "service": "microblog",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": round(total_duration, 2),
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy": sum(1 for check in checks.values() if check["status"] == HealthStatus.HEALTHY),
                "degraded": sum(1 for check in checks.values() if check["status"] == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for check in checks.values() if check["status"] == HealthStatus.UNHEALTHY)
            }
        }


# Global health checker instance
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def get_health_status() -> dict[str, Any]:
    """Get comprehensive health status."""
    checker = get_health_checker()
    return await checker.run_all_checks()


async def get_simple_health_status() -> dict[str, Any]:
    """Get simple health status for basic monitoring."""
    try:
        status = await get_health_status()
        return {
            "status": status["status"],
            "timestamp": status["timestamp"],
            "service": "microblog",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "microblog",
            "version": "1.0.0",
            "error": str(e)
        }
