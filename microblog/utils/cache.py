"""
Performance optimization utilities with template caching, asset optimization, and build performance monitoring.

This module provides caching systems and performance optimization tools for the static site generator,
including template compilation caching, rendered output caching, and performance metrics tracking.
"""

import hashlib
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, TypeVar

from jinja2 import Template

from microblog.server.config import get_config
from microblog.utils.monitoring import (
    get_performance_monitor as get_monitoring_performance_monitor,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStats:
    """Cache statistics tracking."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size = 0
        self._lock = Lock()

    def record_hit(self):
        with self._lock:
            self.hits += 1

    def record_miss(self):
        with self._lock:
            self.misses += 1

    def record_eviction(self):
        with self._lock:
            self.evictions += 1

    def set_size(self, size: int):
        with self._lock:
            self.size = size

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'size': self.size,
                'hit_rate': self.hit_rate
            }


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: dict[str, Any] = {}
        self._access_order: list[str] = []
        self._lock = Lock()
        self.stats = CacheStats()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                self.stats.record_hit()
                return self._cache[key]
            else:
                self.stats.record_miss()
                return None

    def put(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                # Update existing item
                self._cache[key] = value
                self._access_order.remove(key)
                self._access_order.append(key)
            else:
                # Add new item
                if len(self._cache) >= self.max_size:
                    # Evict least recently used
                    oldest_key = self._access_order.pop(0)
                    del self._cache[oldest_key]
                    self.stats.record_eviction()

                self._cache[key] = value
                self._access_order.append(key)

            self.stats.set_size(len(self._cache))

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self.stats.set_size(0)

    def size(self) -> int:
        with self._lock:
            return len(self._cache)


class TemplateCache:
    """Template compilation and output caching system."""

    def __init__(self,
                 compiled_cache_size: int = 50,
                 rendered_cache_size: int = 200,
                 enable_rendered_cache: bool = True):
        self.compiled_cache = LRUCache(compiled_cache_size)
        self.rendered_cache = LRUCache(rendered_cache_size) if enable_rendered_cache else None
        self.template_mtimes: dict[str, float] = {}
        self._lock = Lock()

        logger.info(f"Template cache initialized (compiled: {compiled_cache_size}, "
                   f"rendered: {rendered_cache_size if enable_rendered_cache else 'disabled'})")

    def _get_cache_key(self, template_path: str, context: dict[str, Any] | None = None) -> str:
        """Generate cache key for template and context."""
        if context is None:
            return template_path

        # Create a hash of the context for caching rendered output
        context_str = str(sorted(context.items()))
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{template_path}:{context_hash}"

    def _is_template_modified(self, template_path: Path) -> bool:
        """Check if template file has been modified since last cache."""
        try:
            current_mtime = template_path.stat().st_mtime
            cached_mtime = self.template_mtimes.get(str(template_path))

            if cached_mtime is None or current_mtime > cached_mtime:
                self.template_mtimes[str(template_path)] = current_mtime
                return True
            return False
        except (OSError, FileNotFoundError):
            return True

    def get_compiled_template(self, template_path: Path, template_loader_func: Callable[[], Template]) -> Template:
        """Get compiled template from cache or compile and cache."""
        cache_key = str(template_path)

        # Check if template was modified
        if self._is_template_modified(template_path):
            # Template was modified, invalidate cache
            with self._lock:
                if cache_key in self.compiled_cache._cache:
                    logger.debug(f"Template modified, invalidating cache: {template_path}")
            self.compiled_cache.put(cache_key, None)  # Force miss

        # Try to get from cache
        template = self.compiled_cache.get(cache_key)
        if template is not None:
            return template

        # Load and cache template
        template = template_loader_func()
        self.compiled_cache.put(cache_key, template)
        logger.debug(f"Compiled and cached template: {template_path}")
        return template

    def get_rendered_output(self, template_path: str, context: dict[str, Any] | None = None) -> str | None:
        """Get rendered output from cache."""
        if self.rendered_cache is None:
            return None

        cache_key = self._get_cache_key(template_path, context)
        return self.rendered_cache.get(cache_key)

    def put_rendered_output(self, template_path: str, context: dict[str, Any] | None, output: str):
        """Cache rendered output."""
        if self.rendered_cache is None:
            return

        cache_key = self._get_cache_key(template_path, context)
        self.rendered_cache.put(cache_key, output)
        logger.debug(f"Cached rendered output: {cache_key}")

    def invalidate_template(self, template_path: str):
        """Invalidate all cached data for a template."""
        # Invalidate compiled template
        self.compiled_cache.put(template_path, None)

        # Invalidate all rendered outputs for this template
        if self.rendered_cache is not None:
            with self.rendered_cache._lock:
                keys_to_remove = [key for key in self.rendered_cache._cache.keys()
                                if key.startswith(template_path)]
                for key in keys_to_remove:
                    if key in self.rendered_cache._cache:
                        del self.rendered_cache._cache[key]
                    if key in self.rendered_cache._access_order:
                        self.rendered_cache._access_order.remove(key)

        logger.debug(f"Invalidated template cache: {template_path}")

    def clear_all(self):
        """Clear all caches."""
        self.compiled_cache.clear()
        if self.rendered_cache is not None:
            self.rendered_cache.clear()
        self.template_mtimes.clear()
        logger.info("Cleared all template caches")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'compiled_cache': self.compiled_cache.stats.to_dict(),
        }
        if self.rendered_cache is not None:
            stats['rendered_cache'] = self.rendered_cache.stats.to_dict()
        return stats


class PerformanceTimer:
    """Context manager for measuring execution time."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.duration

        # Log performance metrics
        logger.debug(f"Performance: {self.operation_name} took {duration:.3f}s")

        # Send to monitoring service if available
        try:
            monitoring = get_monitoring_performance_monitor()
            monitoring.record_metric(f"performance_{self.operation_name}", duration)
        except Exception as e:
            logger.debug(f"Failed to record performance metric: {e}")

    @property
    def duration(self) -> float:
        """Get the measured duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


class ParallelProcessor:
    """Utility for parallel processing of build tasks."""

    def __init__(self, max_workers: int | None = None):
        if max_workers is None:
            try:
                config = get_config()
                max_workers = config.performance.max_parallel_workers
            except Exception:
                max_workers = None

        self.max_workers = max_workers or min(4, (Path.cwd().stat().st_size // (1024 * 1024)) + 1)
        logger.info(f"Parallel processor initialized with {self.max_workers} workers")

    def process_in_parallel(self,
                          items: list[T],
                          processor_func: Callable[[T], Any],
                          progress_callback: Callable[[int, int], None] | None = None) -> list[Any]:
        """
        Process items in parallel using ThreadPoolExecutor.

        Args:
            items: List of items to process
            processor_func: Function to process each item
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            List of processing results
        """
        if not items:
            return []

        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item
                for item in items
            }

            # Collect results as they complete
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    item = future_to_item[future]
                    logger.error(f"Failed to process item {item}: {e}")
                    results.append(None)

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(items))

        return results


class BuildPerformanceMonitor:
    """Monitor and track build performance metrics."""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.build_start_time = None
        self.phase_start_times: dict[str, float] = {}
        self._lock = Lock()

    def start_build(self):
        """Mark the start of a build process."""
        self.build_start_time = time.perf_counter()
        self.metrics.clear()
        self.phase_start_times.clear()
        logger.debug("Build performance monitoring started")

    def start_phase(self, phase_name: str):
        """Mark the start of a build phase."""
        self.phase_start_times[phase_name] = time.perf_counter()

    def end_phase(self, phase_name: str):
        """Mark the end of a build phase and record its duration."""
        if phase_name in self.phase_start_times:
            duration = time.perf_counter() - self.phase_start_times[phase_name]
            with self._lock:
                self.metrics[f"{phase_name}_duration"].append(duration)
            logger.debug(f"Phase '{phase_name}' completed in {duration:.3f}s")
            del self.phase_start_times[phase_name]

    def record_metric(self, metric_name: str, value: float):
        """Record a custom performance metric."""
        with self._lock:
            self.metrics[metric_name].append(value)

    def get_build_duration(self) -> float:
        """Get total build duration."""
        if self.build_start_time is None:
            return 0.0
        return time.perf_counter() - self.build_start_time

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all recorded metrics."""
        with self._lock:
            summary = {}
            for metric_name, values in self.metrics.items():
                if values:
                    summary[metric_name] = {
                        'total': sum(values),
                        'average': sum(values) / len(values),
                        'count': len(values),
                        'min': min(values),
                        'max': max(values)
                    }

            summary['total_build_duration'] = self.get_build_duration()
            return summary

    def check_performance_targets(self) -> dict[str, bool]:
        """Check if build meets performance targets."""
        try:
            config = get_config()
            targets = config.performance.build_performance_targets
        except Exception:
            # Fallback to default targets
            targets = {
                'build_time_100_posts': 5.0,  # seconds
                'build_time_1000_posts': 30.0,  # seconds
                'markdown_parsing_per_file': 0.1,  # seconds
                'template_rendering_per_page': 0.05  # seconds
            }

        results = {}
        metrics = self.get_metrics_summary()

        # Check total build time
        total_duration = metrics.get('total_build_duration', 0)
        results['build_time_acceptable'] = total_duration < targets['build_time_100_posts']

        # Check per-file processing times
        if 'content_processing_duration' in metrics:
            avg_processing = metrics['content_processing_duration']['average']
            results['markdown_processing_acceptable'] = avg_processing < targets['markdown_parsing_per_file']

        if 'template_rendering_duration' in metrics:
            avg_rendering = metrics['template_rendering_duration']['average']
            results['template_rendering_acceptable'] = avg_rendering < targets['template_rendering_per_page']

        return results


# Global cache instances
_template_cache: TemplateCache | None = None
_performance_monitor: BuildPerformanceMonitor | None = None


def get_template_cache() -> TemplateCache:
    """Get the global template cache instance."""
    global _template_cache
    if _template_cache is None:
        config = get_config()
        # Use performance configuration settings
        perf_config = config.performance
        _template_cache = TemplateCache(
            compiled_cache_size=perf_config.template_cache_size,
            rendered_cache_size=perf_config.rendered_cache_size,
            enable_rendered_cache=perf_config.enable_rendered_output_caching
        )
    return _template_cache


def get_performance_monitor() -> BuildPerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = BuildPerformanceMonitor()
    return _performance_monitor


def performance_timer(operation_name: str):
    """Decorator for measuring function execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceTimer(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
