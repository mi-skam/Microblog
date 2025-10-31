"""
Structured logging system with JSON formatting, performance tracking, and security logging.

This module provides comprehensive logging capabilities including:
- Structured JSON logging for machine processing
- Performance tracking and timing utilities
- Security event logging
- Audit trail capabilities
- Log level configuration and filtering
"""

import json
import logging
import logging.handlers
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from microblog.utils import get_content_dir


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats log records as JSON with consistent structure:
    - timestamp: ISO format timestamp
    - level: Log level (DEBUG, INFO, WARN, ERROR)
    - module: Logger name/module
    - message: Log message
    - extra: Any additional fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage()
        }

        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class SecurityLogger:
    """
    Specialized logger for security events.

    Provides methods for logging security-relevant events like:
    - Authentication failures
    - CSRF violations
    - Permission errors
    - Suspicious activity
    """

    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)

    def auth_failure(self, user_id: str | None, ip_address: str, reason: str):
        """Log authentication failure."""
        self.logger.warning(
            "Authentication failure",
            extra={
                "event_type": "auth_failure",
                "user_id": user_id,
                "ip_address": ip_address,
                "reason": reason
            }
        )

    def csrf_violation(self, ip_address: str, path: str, user_agent: str):
        """Log CSRF violation."""
        self.logger.warning(
            "CSRF token violation",
            extra={
                "event_type": "csrf_violation",
                "ip_address": ip_address,
                "path": path,
                "user_agent": user_agent
            }
        )

    def permission_denied(self, user_id: str | None, resource: str, action: str):
        """Log permission denied events."""
        self.logger.warning(
            "Permission denied",
            extra={
                "event_type": "permission_denied",
                "user_id": user_id,
                "resource": resource,
                "action": action
            }
        )

    def suspicious_activity(self, description: str, metadata: dict[str, Any]):
        """Log suspicious activity."""
        self.logger.warning(
            f"Suspicious activity: {description}",
            extra={
                "event_type": "suspicious_activity",
                **metadata
            }
        )


class PerformanceLogger:
    """
    Performance tracking and timing utilities.

    Provides context managers and decorators for tracking:
    - Function execution times
    - Build operation durations
    - API response times
    - Resource usage
    """

    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)

    @contextmanager
    def track_operation(self, operation_name: str, metadata: dict[str, Any] | None = None):
        """
        Context manager for tracking operation duration.

        Args:
            operation_name: Name of the operation being tracked
            metadata: Additional metadata to include in log
        """
        start_time = time.time()
        metadata = metadata or {}

        try:
            yield
            duration = time.time() - start_time
            self.logger.info(
                f"Operation completed: {operation_name}",
                extra={
                    "event_type": "performance",
                    "operation": operation_name,
                    "duration_seconds": round(duration, 3),
                    "status": "success",
                    **metadata
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    "event_type": "performance",
                    "operation": operation_name,
                    "duration_seconds": round(duration, 3),
                    "status": "error",
                    "error": str(e),
                    **metadata
                }
            )
            raise

    def time_function(self, include_args: bool = False):
        """
        Decorator for timing function execution.

        Args:
            include_args: Whether to include function arguments in log
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                func_name = f"{func.__module__}.{func.__name__}"

                metadata = {"function": func_name}
                if include_args:
                    metadata["args"] = str(args)
                    metadata["kwargs"] = str(kwargs)

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.logger.info(
                        f"Function completed: {func_name}",
                        extra={
                            "event_type": "performance",
                            "operation_type": "function_call",
                            "duration_seconds": round(duration, 3),
                            "status": "success",
                            **metadata
                        }
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.error(
                        f"Function failed: {func_name}",
                        extra={
                            "event_type": "performance",
                            "operation_type": "function_call",
                            "duration_seconds": round(duration, 3),
                            "status": "error",
                            "error": str(e),
                            **metadata
                        }
                    )
                    raise
            return wrapper
        return decorator


class AuditLogger:
    """
    Audit trail logging for tracking user actions and system changes.

    Provides methods for logging:
    - Content modifications
    - User actions
    - Configuration changes
    - System events
    """

    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)

    def content_modified(self, user_id: str, content_type: str, content_id: str, action: str):
        """Log content modification events."""
        self.logger.info(
            f"Content {action}: {content_type}",
            extra={
                "event_type": "content_modification",
                "user_id": user_id,
                "content_type": content_type,
                "content_id": content_id,
                "action": action
            }
        )

    def user_action(self, user_id: str, action: str, resource: str, metadata: dict[str, Any] | None = None):
        """Log user actions."""
        log_data = {
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            "resource": resource
        }
        if metadata:
            log_data.update(metadata)

        self.logger.info(f"User action: {action} on {resource}", extra=log_data)

    def config_changed(self, user_id: str | None, config_key: str, old_value: Any, new_value: Any):
        """Log configuration changes."""
        self.logger.info(
            f"Configuration changed: {config_key}",
            extra={
                "event_type": "config_change",
                "user_id": user_id,
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value)
            }
        )

    def system_event(self, event_type: str, description: str, metadata: dict[str, Any] | None = None):
        """Log system events."""
        log_data = {
            "event_type": "system_event",
            "system_event_type": event_type,
        }
        if metadata:
            log_data.update(metadata)
        self.logger.info(f"System event: {description}", extra=log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> None:
    """
    Set up structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file. If None, defaults to content_dir/logs/microblog.log
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to also output logs to console
    """
    # Set up log file path
    if log_file is None:
        log_dir = get_content_dir() / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "microblog.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create structured formatter
    formatter = StructuredFormatter()

    # Set up file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set up console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Configure specific loggers
    security_logger = logging.getLogger("security")
    performance_logger = logging.getLogger("performance")
    audit_logger = logging.getLogger("audit")

    # Set appropriate levels
    security_logger.setLevel(logging.WARNING)
    performance_logger.setLevel(logging.INFO)
    audit_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def get_security_logger() -> SecurityLogger:
    """Get the security logger instance."""
    return SecurityLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger instance."""
    return PerformanceLogger()


def get_audit_logger() -> AuditLogger:
    """Get the audit logger instance."""
    return AuditLogger()


# Performance tracking decorators for common use cases
def track_build_performance(func):
    """Decorator for tracking build operation performance."""
    performance_logger = get_performance_logger()
    return performance_logger.time_function(include_args=False)(func)


def track_api_performance(func):
    """Decorator for tracking API endpoint performance."""
    performance_logger = get_performance_logger()
    return performance_logger.time_function(include_args=True)(func)
