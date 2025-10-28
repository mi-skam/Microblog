"""
Build service for background processing and queue management.

This module provides a service layer for managing build operations with
background processing, progress tracking, and queue management to prevent
concurrent builds.
"""

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from uuid import uuid4

from microblog.builder.generator import BuildProgress, BuildResult, build_site

logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status enumeration for tracking build states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildJobInfo:
    """Information about a build job."""

    def __init__(self, job_id: str, user_id: str = None):
        self.job_id = job_id
        self.user_id = user_id
        self.status = BuildStatus.QUEUED
        self.created_at = datetime.now()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.progress_history: list[BuildProgress] = []
        self.current_progress: BuildProgress | None = None
        self.result: BuildResult | None = None
        self.error_message: str | None = None


class BuildService:
    """
    Service for managing build operations with background processing.

    Features:
    - Background build processing
    - Build queue management
    - Real-time progress tracking
    - Build status monitoring
    - Concurrent build prevention
    """

    def __init__(self):
        self._jobs: dict[str, BuildJobInfo] = {}
        self._current_job_id: str | None = None
        self._build_lock = threading.Lock()
        self._executor_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._progress_callbacks: dict[str, list[Callable[[BuildProgress], None]]] = {}

        logger.info("Build service initialized")

    def _progress_callback_wrapper(self, job_id: str) -> Callable[[BuildProgress], None]:
        """
        Create a progress callback wrapper for a specific job.

        Args:
            job_id: Job ID to track progress for

        Returns:
            Progress callback function
        """
        def callback(progress: BuildProgress) -> None:
            """Internal progress callback that updates job progress and notifies subscribers."""
            try:
                if job_id in self._jobs:
                    job = self._jobs[job_id]
                    job.current_progress = progress
                    job.progress_history.append(progress)

                    # Notify all subscribers for this job
                    if job_id in self._progress_callbacks:
                        for subscriber_callback in self._progress_callbacks[job_id]:
                            try:
                                subscriber_callback(progress)
                            except Exception as e:
                                logger.warning(f"Progress callback error for job {job_id}: {e}")

                    logger.debug(f"Build progress for job {job_id}: {progress.phase.value} - {progress.message} ({progress.percentage:.1f}%)")

            except Exception as e:
                logger.error(f"Error in progress callback wrapper for job {job_id}: {e}")

        return callback

    def _execute_build(self, job_id: str) -> None:
        """
        Execute a build job in the background.

        Args:
            job_id: Job ID to execute
        """
        try:
            job = self._jobs.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found for execution")
                return

            logger.info(f"Starting build execution for job {job_id}")
            job.status = BuildStatus.RUNNING
            job.started_at = datetime.now()

            # Create progress callback for this job
            progress_callback = self._progress_callback_wrapper(job_id)

            # Execute the actual build
            result = build_site(progress_callback)

            # Update job with result
            job.result = result
            job.completed_at = datetime.now()

            if result.success:
                job.status = BuildStatus.COMPLETED
                logger.info(f"Build job {job_id} completed successfully in {result.duration:.1f}s")
            else:
                job.status = BuildStatus.FAILED
                job.error_message = result.message
                logger.error(f"Build job {job_id} failed: {result.message}")

        except Exception as e:
            # Handle unexpected errors
            job = self._jobs.get(job_id)
            if job:
                job.status = BuildStatus.FAILED
                job.error_message = f"Unexpected error: {str(e)}"
                job.completed_at = datetime.now()

            logger.error(f"Unexpected error in build execution for job {job_id}: {e}")

        finally:
            # Clear current job and release lock
            with self._build_lock:
                if self._current_job_id == job_id:
                    self._current_job_id = None

            logger.debug(f"Build execution finished for job {job_id}")

    def _build_executor(self) -> None:
        """
        Background thread that processes queued build jobs.

        This runs continuously and processes jobs from the queue one at a time.
        """
        logger.info("Build executor thread started")

        while not self._shutdown_event.is_set():
            try:
                # Look for queued jobs
                next_job_id = None

                with self._build_lock:
                    if self._current_job_id is None:
                        # Find the oldest queued job
                        queued_jobs = [
                            (job_id, job) for job_id, job in self._jobs.items()
                            if job.status == BuildStatus.QUEUED
                        ]

                        if queued_jobs:
                            # Sort by creation time and take the oldest
                            queued_jobs.sort(key=lambda x: x[1].created_at)
                            next_job_id = queued_jobs[0][0]
                            self._current_job_id = next_job_id

                if next_job_id:
                    # Execute the next job
                    self._execute_build(next_job_id)
                else:
                    # No jobs to process, wait a bit
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in build executor: {e}")
                # Continue running even if there's an error
                time.sleep(1)

        logger.info("Build executor thread stopped")

    def start_executor(self) -> None:
        """Start the background build executor if not already running."""
        if self._executor_thread is None or not self._executor_thread.is_alive():
            self._shutdown_event.clear()
            self._executor_thread = threading.Thread(target=self._build_executor, daemon=True)
            self._executor_thread.start()
            logger.info("Build executor started")

    def stop_executor(self) -> None:
        """Stop the background build executor."""
        if self._executor_thread and self._executor_thread.is_alive():
            self._shutdown_event.set()
            self._executor_thread.join(timeout=5)
            logger.info("Build executor stopped")

    def queue_build(self, user_id: str = None) -> str:
        """
        Queue a new build job.

        Args:
            user_id: Optional user ID who requested the build

        Returns:
            Job ID for tracking the build

        Raises:
            RuntimeError: If there are too many queued jobs
        """
        # Check if we have too many queued jobs (prevent spam)
        queued_count = sum(1 for job in self._jobs.values() if job.status == BuildStatus.QUEUED)
        if queued_count >= 5:
            raise RuntimeError("Too many builds queued. Please wait for current builds to complete.")

        # Generate unique job ID
        job_id = str(uuid4())

        # Create job info
        job = BuildJobInfo(job_id, user_id)
        self._jobs[job_id] = job

        # Ensure executor is running
        self.start_executor()

        logger.info(f"Build job {job_id} queued by user {user_id or 'unknown'}")
        return job_id

    def get_job_status(self, job_id: str) -> BuildJobInfo | None:
        """
        Get the status of a build job.

        Args:
            job_id: Job ID to check

        Returns:
            BuildJobInfo if job exists, None otherwise
        """
        return self._jobs.get(job_id)

    def get_current_build(self) -> BuildJobInfo | None:
        """
        Get information about the currently running build.

        Returns:
            BuildJobInfo if a build is running, None otherwise
        """
        if self._current_job_id:
            return self._jobs.get(self._current_job_id)
        return None

    def get_build_queue(self) -> list[BuildJobInfo]:
        """
        Get list of all queued builds.

        Returns:
            List of BuildJobInfo objects for queued builds
        """
        return [
            job for job in self._jobs.values()
            if job.status == BuildStatus.QUEUED
        ]

    def get_recent_builds(self, limit: int = 10) -> list[BuildJobInfo]:
        """
        Get list of recent builds (completed or failed).

        Args:
            limit: Maximum number of builds to return

        Returns:
            List of BuildJobInfo objects sorted by completion time
        """
        completed_builds = [
            job for job in self._jobs.values()
            if job.status in [BuildStatus.COMPLETED, BuildStatus.FAILED]
        ]

        # Sort by completion time (most recent first)
        completed_builds.sort(key=lambda x: x.completed_at or datetime.min, reverse=True)

        return completed_builds[:limit]

    def subscribe_to_progress(self, job_id: str, callback: Callable[[BuildProgress], None]) -> None:
        """
        Subscribe to progress updates for a specific job.

        Args:
            job_id: Job ID to subscribe to
            callback: Function to call with progress updates
        """
        if job_id not in self._progress_callbacks:
            self._progress_callbacks[job_id] = []

        self._progress_callbacks[job_id].append(callback)
        logger.debug(f"Added progress subscriber for job {job_id}")

    def unsubscribe_from_progress(self, job_id: str, callback: Callable[[BuildProgress], None]) -> None:
        """
        Unsubscribe from progress updates for a specific job.

        Args:
            job_id: Job ID to unsubscribe from
            callback: Function to remove from subscribers
        """
        if job_id in self._progress_callbacks:
            try:
                self._progress_callbacks[job_id].remove(callback)
                if not self._progress_callbacks[job_id]:
                    del self._progress_callbacks[job_id]
                logger.debug(f"Removed progress subscriber for job {job_id}")
            except ValueError:
                # Callback not in list
                pass

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued build job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if job was cancelled, False if job not found or already running
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status == BuildStatus.QUEUED:
            job.status = BuildStatus.CANCELLED
            job.completed_at = datetime.now()
            logger.info(f"Build job {job_id} cancelled")
            return True

        # Cannot cancel running jobs
        return False

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed/failed jobs to prevent memory buildup.

        Args:
            max_age_hours: Maximum age in hours for keeping job history

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        jobs_to_remove = []

        for job_id, job in self._jobs.items():
            if job.status in [BuildStatus.COMPLETED, BuildStatus.FAILED, BuildStatus.CANCELLED]:
                if job.completed_at and job.completed_at.timestamp() < cutoff_time:
                    jobs_to_remove.append(job_id)

        # Remove old jobs
        for job_id in jobs_to_remove:
            del self._jobs[job_id]
            # Also remove any remaining progress callbacks
            if job_id in self._progress_callbacks:
                del self._progress_callbacks[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old build jobs")

        return len(jobs_to_remove)


# Global build service instance
_build_service: BuildService | None = None


def get_build_service() -> BuildService:
    """
    Get the global build service instance.

    Returns:
        BuildService instance
    """
    global _build_service
    if _build_service is None:
        _build_service = BuildService()
    return _build_service
