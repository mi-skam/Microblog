"""
Monitoring utilities for performance tracking, metrics collection, and alerting.

This module provides comprehensive monitoring capabilities including:
- Performance metrics collection
- Resource usage tracking
- Build monitoring
- API response time tracking
- Error tracking and alerting
- System resource monitoring
"""

import asyncio
import logging
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class MetricType:
    """Metric type constants."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class Metric:
    """Individual metric with timestamp and metadata."""

    def __init__(self, name: str, value: int | float, metric_type: str, labels: dict[str, str] | None = None, timestamp: datetime | None = None):
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCollector:
    """
    Thread-safe metrics collection system.

    Collects and stores metrics with automatic cleanup of old data.
    Supports counters, gauges, histograms, and timers.
    """

    def __init__(self, max_metrics_per_type: int = 1000, retention_hours: int = 24):
        self._metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_per_type))
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        self.retention_hours = retention_hours

    def increment_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._add_metric(Metric(name, self._counters[key], MetricType.COUNTER, labels))

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Set a gauge metric value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._add_metric(Metric(name, value, MetricType.GAUGE, labels))

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Record a histogram value."""
        with self._lock:
            self._add_metric(Metric(name, value, MetricType.HISTOGRAM, labels))

    def record_timer(self, name: str, duration_seconds: float, labels: dict[str, str] | None = None):
        """Record a timer duration."""
        with self._lock:
            self._add_metric(Metric(name, duration_seconds, MetricType.TIMER, labels))

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a unique key for metric storage."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"

    def _add_metric(self, metric: Metric):
        """Add metric to storage (assumes lock is held)."""
        self._metrics[metric.name].append(metric)

    def get_metrics(self, name: str | None = None, since: datetime | None = None) -> list[Metric]:
        """Get metrics, optionally filtered by name and time."""
        with self._lock:
            metrics = []
            cutoff_time = since or (datetime.utcnow() - timedelta(hours=self.retention_hours))

            metric_names = [name] if name else self._metrics.keys()

            for metric_name in metric_names:
                if metric_name in self._metrics:
                    for metric in self._metrics[metric_name]:
                        if metric.timestamp >= cutoff_time:
                            metrics.append(metric)

            return sorted(metrics, key=lambda m: m.timestamp)

    def get_current_counters(self) -> dict[str, float]:
        """Get current counter values."""
        with self._lock:
            return dict(self._counters)

    def get_current_gauges(self) -> dict[str, float]:
        """Get current gauge values."""
        with self._lock:
            return dict(self._gauges)

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

        with self._lock:
            for _name, metric_deque in self._metrics.items():
                # Remove old metrics from the front of the deque
                while metric_deque and metric_deque[0].timestamp < cutoff_time:
                    metric_deque.popleft()

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics of all metrics."""
        with self._lock:
            summary = {
                "total_metrics": sum(len(deque_) for deque_ in self._metrics.values()),
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "metric_types": list(self._metrics.keys()),
                "retention_hours": self.retention_hours
            }
            return summary


class PerformanceMonitor:
    """
    Performance monitoring system for tracking operation durations and resource usage.

    Provides context managers and decorators for automatic performance tracking.
    """

    def __init__(self, metrics_collector: MetricsCollector | None = None):
        self.metrics = metrics_collector or MetricsCollector()

    @contextmanager
    def track_operation(self, operation_name: str, labels: dict[str, str] | None = None):
        """
        Context manager for tracking operation performance.

        Args:
            operation_name: Name of the operation
            labels: Additional labels for the metric
        """
        start_time = time.time()
        start_memory = None

        if PSUTIL_AVAILABLE:
            try:
                start_memory = psutil.Process().memory_info().rss
            except Exception:
                pass

        try:
            yield
            # Operation succeeded
            duration = time.time() - start_time

            # Record performance metrics
            self.metrics.record_timer(f"{operation_name}.duration", duration, labels)
            self.metrics.increment_counter(f"{operation_name}.success", 1.0, labels)

            # Record memory delta if psutil is available
            if PSUTIL_AVAILABLE and start_memory is not None:
                try:
                    end_memory = psutil.Process().memory_info().rss
                    memory_delta = end_memory - start_memory
                    self.metrics.record_histogram(f"{operation_name}.memory_delta", memory_delta, labels)
                except Exception:
                    pass

        except Exception as e:
            # Operation failed
            duration = time.time() - start_time
            error_labels = {**(labels or {}), "error_type": type(e).__name__}

            self.metrics.record_timer(f"{operation_name}.duration", duration, error_labels)
            self.metrics.increment_counter(f"{operation_name}.error", 1.0, error_labels)
            raise

    def track_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Track API request performance."""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code)
        }

        self.metrics.record_timer("api.request.duration", duration, labels)
        self.metrics.increment_counter("api.request.total", 1.0, labels)

        if 200 <= status_code < 300:
            self.metrics.increment_counter("api.request.success", 1.0, labels)
        elif 400 <= status_code < 500:
            self.metrics.increment_counter("api.request.client_error", 1.0, labels)
        elif 500 <= status_code < 600:
            self.metrics.increment_counter("api.request.server_error", 1.0, labels)

    def track_build_operation(self, operation: str, duration: float, success: bool, metadata: dict[str, Any] | None = None):
        """Track build operation performance."""
        labels = {
            "operation": operation,
            "status": "success" if success else "failure"
        }

        if metadata:
            # Add safe metadata as labels (convert to strings)
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    labels[f"meta_{key}"] = str(value)

        self.metrics.record_timer("build.operation.duration", duration, labels)
        self.metrics.increment_counter("build.operation.total", 1.0, labels)

        if success:
            self.metrics.increment_counter("build.operation.success", 1.0, labels)
        else:
            self.metrics.increment_counter("build.operation.failure", 1.0, labels)


class SystemMonitor:
    """
    System resource monitoring.

    Tracks CPU, memory, disk usage, and other system metrics.
    """

    def __init__(self, metrics_collector: MetricsCollector | None = None):
        self.metrics = metrics_collector or MetricsCollector()

    def collect_system_metrics(self):
        """Collect current system metrics."""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available - system metrics collection disabled")
            return

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.set_gauge("system.cpu.percent", cpu_percent)

            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics.set_gauge("system.memory.total", memory.total)
            self.metrics.set_gauge("system.memory.available", memory.available)
            self.metrics.set_gauge("system.memory.percent", memory.percent)

            # Disk metrics - use current directory if root not available
            try:
                disk = psutil.disk_usage('/')
            except Exception:
                disk = psutil.disk_usage('.')

            self.metrics.set_gauge("system.disk.total", disk.total)
            self.metrics.set_gauge("system.disk.free", disk.free)
            self.metrics.set_gauge("system.disk.percent", (disk.used / disk.total) * 100)

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self.metrics.set_gauge("process.memory.rss", process_memory.rss)
            self.metrics.set_gauge("process.memory.vms", process_memory.vms)

            try:
                self.metrics.set_gauge("process.cpu.percent", process.cpu_percent())
            except Exception:
                pass  # CPU percent might not be available immediately

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")


class AlertManager:
    """
    Simple alerting system for monitoring thresholds.

    Tracks conditions and triggers alerts when thresholds are exceeded.
    """

    def __init__(self, metrics_collector: MetricsCollector | None = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.alert_conditions: list[dict[str, Any]] = []
        self.active_alerts: dict[str, dict[str, Any]] = {}

    def add_alert_condition(self, name: str, metric_name: str, threshold: float, operator: str = "greater_than", labels: dict[str, str] | None = None):
        """
        Add an alert condition.

        Args:
            name: Alert name
            metric_name: Metric to monitor
            threshold: Threshold value
            operator: Comparison operator (greater_than, less_than, equals)
            labels: Labels to filter metrics
        """
        condition = {
            "name": name,
            "metric_name": metric_name,
            "threshold": threshold,
            "operator": operator,
            "labels": labels or {}
        }
        self.alert_conditions.append(condition)

    def check_alerts(self) -> list[dict[str, Any]]:
        """Check all alert conditions and return active alerts."""
        current_alerts = []

        for condition in self.alert_conditions:
            # Get recent metrics for this condition
            recent_metrics = self.metrics.get_metrics(
                condition["metric_name"],
                since=datetime.utcnow() - timedelta(minutes=5)
            )

            # Filter by labels if specified
            if condition["labels"]:
                recent_metrics = [
                    m for m in recent_metrics
                    if all(m.labels.get(k) == v for k, v in condition["labels"].items())
                ]

            if not recent_metrics:
                continue

            # Get the latest metric value
            latest_metric = recent_metrics[-1]
            alert_triggered = False

            if condition["operator"] == "greater_than":
                alert_triggered = latest_metric.value > condition["threshold"]
            elif condition["operator"] == "less_than":
                alert_triggered = latest_metric.value < condition["threshold"]
            elif condition["operator"] == "equals":
                alert_triggered = latest_metric.value == condition["threshold"]

            if alert_triggered:
                alert = {
                    "name": condition["name"],
                    "metric_name": condition["metric_name"],
                    "current_value": latest_metric.value,
                    "threshold": condition["threshold"],
                    "operator": condition["operator"],
                    "timestamp": latest_metric.timestamp.isoformat(),
                    "labels": latest_metric.labels
                }
                current_alerts.append(alert)
                self.active_alerts[condition["name"]] = alert

        return current_alerts

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get currently active alerts."""
        return list(self.active_alerts.values())


# Global monitoring instances
_metrics_collector: MetricsCollector | None = None
_performance_monitor: PerformanceMonitor | None = None
_system_monitor: SystemMonitor | None = None
_alert_manager: AlertManager | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(get_metrics_collector())
    return _performance_monitor


def get_system_monitor() -> SystemMonitor:
    """Get the global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(get_metrics_collector())
    return _system_monitor


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(get_metrics_collector())
        _setup_default_alerts(_alert_manager)
    return _alert_manager


def _setup_default_alerts(alert_manager: AlertManager):
    """Set up default alert conditions."""
    # High CPU usage
    alert_manager.add_alert_condition(
        "high_cpu_usage",
        "system.cpu.percent",
        80.0,
        "greater_than"
    )

    # High memory usage
    alert_manager.add_alert_condition(
        "high_memory_usage",
        "system.memory.percent",
        85.0,
        "greater_than"
    )

    # Low disk space
    alert_manager.add_alert_condition(
        "low_disk_space",
        "system.disk.percent",
        90.0,
        "greater_than"
    )

    # High API error rate (if more than 10% of requests fail)
    alert_manager.add_alert_condition(
        "high_api_error_rate",
        "api.request.server_error",
        10.0,
        "greater_than"
    )


async def start_monitoring_background_tasks():
    """Start background monitoring tasks."""
    system_monitor = get_system_monitor()
    metrics_collector = get_metrics_collector()

    async def system_metrics_task():
        """Background task to collect system metrics."""
        while True:
            try:
                system_monitor.collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logger.error(f"Error in system metrics collection: {e}")
                await asyncio.sleep(60)  # Longer delay on error

    async def cleanup_task():
        """Background task to clean up old metrics."""
        while True:
            try:
                metrics_collector.cleanup_old_metrics()
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
                await asyncio.sleep(3600)

    # Start background tasks
    asyncio.create_task(system_metrics_task())
    asyncio.create_task(cleanup_task())


def get_monitoring_summary() -> dict[str, Any]:
    """Get a comprehensive monitoring summary."""
    metrics_collector = get_metrics_collector()
    alert_manager = get_alert_manager()

    return {
        "metrics_summary": metrics_collector.get_summary(),
        "active_alerts": alert_manager.get_active_alerts(),
        "current_counters": metrics_collector.get_current_counters(),
        "current_gauges": metrics_collector.get_current_gauges(),
        "timestamp": datetime.utcnow().isoformat()
    }

