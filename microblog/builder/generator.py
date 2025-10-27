"""
Build generator that orchestrates the complete build process with atomic operations,
backup creation, and rollback capability.

This module provides the main build orchestrator that coordinates markdown processing,
template rendering, and asset copying with safety mechanisms and progress tracking.
"""

import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from microblog.builder.asset_manager import get_asset_manager
from microblog.builder.markdown_processor import get_markdown_processor
from microblog.builder.template_renderer import get_template_renderer
from microblog.content.post_service import get_post_service
from microblog.server.config import get_config
from microblog.utils import ensure_directory

logger = logging.getLogger(__name__)


class BuildPhase(Enum):
    """Build phase enumeration for progress tracking."""
    INITIALIZING = "initializing"
    BACKUP_CREATION = "backup_creation"
    CONTENT_PROCESSING = "content_processing"
    TEMPLATE_RENDERING = "template_rendering"
    ASSET_COPYING = "asset_copying"
    VERIFICATION = "verification"
    CLEANUP = "cleanup"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildProgress:
    """Build progress information for tracking and reporting."""
    phase: BuildPhase
    message: str
    percentage: float = 0.0
    details: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    message: str
    duration: float = 0.0
    build_dir: Path | None = None
    backup_dir: Path | None = None
    progress_history: list[BuildProgress] | None = None
    stats: dict[str, Any] | None = None
    error: Exception | None = None


class BuildGeneratingError(Exception):
    """Raised when build generation fails."""
    pass


class BuildGenerator:
    """
    Build generator that orchestrates the complete static site generation process.

    Features:
    - Atomic build operations with backup and rollback
    - Progress tracking and status reporting
    - Comprehensive error handling and logging
    - Build integrity verification
    - Component coordination (markdown, templates, assets)
    - Safety mechanisms for production use
    """

    def __init__(self, progress_callback: Callable[[BuildProgress], None] | None = None):
        """
        Initialize the build generator.

        Args:
            progress_callback: Optional callback function for progress updates
        """
        self.config = get_config()
        self.markdown_processor = get_markdown_processor()
        self.template_renderer = get_template_renderer()
        self.asset_manager = get_asset_manager()
        self.post_service = get_post_service()

        self.build_dir = Path(self.config.build.output_dir)
        self.backup_dir = Path(self.config.build.backup_dir)

        self.progress_callback = progress_callback
        self.progress_history: list[BuildProgress] = []
        self.build_start_time: datetime | None = None

        logger.info("Build generator initialized")

    def _report_progress(self, phase: BuildPhase, message: str, percentage: float = 0.0, details: dict[str, Any] | None = None):
        """
        Report build progress and execute callback if provided.

        Args:
            phase: Current build phase
            message: Progress message
            percentage: Completion percentage (0-100)
            details: Additional progress details
        """
        progress = BuildProgress(
            phase=phase,
            message=message,
            percentage=percentage,
            details=details or {}
        )

        self.progress_history.append(progress)
        logger.info(f"Build progress: {phase.value} - {message} ({percentage:.1f}%)")

        if self.progress_callback:
            try:
                self.progress_callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _validate_build_preconditions(self) -> bool:
        """
        Validate that all preconditions for building are met.

        Returns:
            True if preconditions are met, False otherwise
        """
        try:
            # Check if content directory exists
            content_dir = self.post_service.posts_dir.parent
            if not content_dir.exists():
                logger.error(f"Content directory does not exist: {content_dir}")
                return False

            # Check if templates directory exists
            templates_dir = self.template_renderer.templates_dir
            if not templates_dir.exists():
                logger.error(f"Templates directory does not exist: {templates_dir}")
                return False

            # Validate required templates exist
            required_templates = ['index.html', 'post.html', 'archive.html', 'rss.xml']
            for template_name in required_templates:
                is_valid, error = self.template_renderer.validate_template(template_name)
                if not is_valid:
                    logger.error(f"Required template '{template_name}' is invalid: {error}")
                    return False

            # Check if we have write permissions for build directory
            build_parent = self.build_dir.parent
            if not build_parent.exists():
                try:
                    ensure_directory(build_parent)
                except Exception as e:
                    logger.error(f"Cannot create build parent directory: {e}")
                    return False

            logger.info("Build preconditions validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating build preconditions: {e}")
            return False

    def _create_backup(self) -> bool:
        """
        Create backup of existing build directory.

        Returns:
            True if backup was created successfully, False otherwise
        """
        try:
            # Remove old backup if it exists
            if self.backup_dir.exists():
                logger.info(f"Removing old backup: {self.backup_dir}")
                shutil.rmtree(self.backup_dir)

            # If build directory exists, move it to backup location
            if self.build_dir.exists():
                logger.info(f"Creating backup: {self.build_dir} -> {self.backup_dir}")
                shutil.move(str(self.build_dir), str(self.backup_dir))
                logger.info("Backup created successfully")
            else:
                logger.info("No existing build directory to backup")

            # Create fresh build directory
            ensure_directory(self.build_dir)
            logger.info(f"Created fresh build directory: {self.build_dir}")

            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _rollback_from_backup(self) -> bool:
        """
        Rollback to backup if it exists.

        Returns:
            True if rollback was successful, False otherwise
        """
        try:
            # Remove failed build directory
            if self.build_dir.exists():
                logger.info(f"Removing failed build directory: {self.build_dir}")
                shutil.rmtree(self.build_dir)

            # Restore from backup if it exists
            if self.backup_dir.exists():
                logger.info(f"Restoring from backup: {self.backup_dir} -> {self.build_dir}")
                shutil.move(str(self.backup_dir), str(self.build_dir))
                logger.info("Rollback completed successfully")
                return True
            else:
                logger.warning("No backup exists to rollback to")
                return False

        except Exception as e:
            logger.error(f"Failed to rollback from backup: {e}")
            return False

    def _process_content(self) -> tuple[list, dict[str, Any]]:
        """
        Process all markdown content to HTML.

        Returns:
            Tuple of (processed_posts, processing_stats)

        Raises:
            BuildGeneratingError: If content processing fails
        """
        try:
            # Get all published posts
            posts = self.post_service.get_published_posts()
            logger.info(f"Found {len(posts)} published posts to process")

            if not posts:
                logger.warning("No published posts found")

            processed_posts = []
            processing_errors = 0

            for i, post in enumerate(posts):
                try:
                    # Process markdown content
                    html_content = self.markdown_processor.process_content(post)

                    processed_posts.append({
                        'post': post,
                        'html_content': html_content
                    })

                    # Report progress
                    progress = ((i + 1) / len(posts)) * 100 if posts else 100
                    self._report_progress(
                        BuildPhase.CONTENT_PROCESSING,
                        f"Processed post: {post.frontmatter.title}",
                        progress,
                        {'processed': i + 1, 'total': len(posts)}
                    )

                except Exception as e:
                    logger.error(f"Failed to process post '{post.frontmatter.title}': {e}")
                    processing_errors += 1

            if processing_errors > 0:
                raise BuildGeneratingError(f"Failed to process {processing_errors} posts")

            stats = {
                'total_posts': len(posts),
                'processed_posts': len(processed_posts),
                'processing_errors': processing_errors
            }

            logger.info(f"Content processing completed: {len(processed_posts)} posts processed")
            return processed_posts, stats

        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            raise BuildGeneratingError(f"Content processing failed: {e}") from e

    def _render_templates(self, processed_posts: list) -> dict[str, Any]:
        """
        Render all templates and generate static pages.

        Args:
            processed_posts: List of processed post data

        Returns:
            Dictionary with rendering statistics

        Raises:
            BuildGeneratingError: If template rendering fails
        """
        try:
            posts = [item['post'] for item in processed_posts]
            rendering_stats = {
                'pages_rendered': 0,
                'rendering_errors': 0,
                'rendered_pages': []
            }

            # Render homepage
            try:
                homepage_html = self.template_renderer.render_homepage(posts)
                homepage_path = self.build_dir / 'index.html'
                with open(homepage_path, 'w', encoding='utf-8') as f:
                    f.write(homepage_html)
                rendering_stats['pages_rendered'] += 1
                rendering_stats['rendered_pages'].append('index.html')
                logger.info("Rendered homepage")

                self._report_progress(
                    BuildPhase.TEMPLATE_RENDERING,
                    "Rendered homepage",
                    10
                )
            except Exception as e:
                logger.error(f"Failed to render homepage: {e}")
                rendering_stats['rendering_errors'] += 1

            # Render individual posts
            posts_dir = self.build_dir / 'posts'
            ensure_directory(posts_dir)

            for i, item in enumerate(processed_posts):
                try:
                    post = item['post']
                    html_content = item['html_content']

                    post_html = self.template_renderer.render_post(post, html_content)
                    post_path = posts_dir / f"{post.computed_slug}.html"

                    with open(post_path, 'w', encoding='utf-8') as f:
                        f.write(post_html)

                    rendering_stats['pages_rendered'] += 1
                    rendering_stats['rendered_pages'].append(f"posts/{post.computed_slug}.html")

                    # Report progress
                    progress = 10 + ((i + 1) / len(processed_posts)) * 60
                    self._report_progress(
                        BuildPhase.TEMPLATE_RENDERING,
                        f"Rendered post: {post.frontmatter.title}",
                        progress
                    )

                except Exception as e:
                    logger.error(f"Failed to render post '{post.frontmatter.title}': {e}")
                    rendering_stats['rendering_errors'] += 1

            # Render archive page
            try:
                archive_html = self.template_renderer.render_archive(posts)
                archive_path = self.build_dir / 'archive.html'
                with open(archive_path, 'w', encoding='utf-8') as f:
                    f.write(archive_html)
                rendering_stats['pages_rendered'] += 1
                rendering_stats['rendered_pages'].append('archive.html')
                logger.info("Rendered archive page")

                self._report_progress(
                    BuildPhase.TEMPLATE_RENDERING,
                    "Rendered archive page",
                    80
                )
            except Exception as e:
                logger.error(f"Failed to render archive page: {e}")
                rendering_stats['rendering_errors'] += 1

            # Render tag pages
            all_tags = self.template_renderer.get_all_tags()
            if all_tags:
                tags_dir = self.build_dir / 'tags'
                ensure_directory(tags_dir)

                for tag in all_tags:
                    try:
                        tag_posts = [p for p in posts if tag.lower() in [t.lower() for t in p.frontmatter.tags]]
                        tag_html = self.template_renderer.render_tag_page(tag, tag_posts)
                        tag_path = tags_dir / f"{tag.lower()}.html"

                        with open(tag_path, 'w', encoding='utf-8') as f:
                            f.write(tag_html)

                        rendering_stats['pages_rendered'] += 1
                        rendering_stats['rendered_pages'].append(f"tags/{tag.lower()}.html")

                    except Exception as e:
                        logger.error(f"Failed to render tag page '{tag}': {e}")
                        rendering_stats['rendering_errors'] += 1

            # Render RSS feed
            try:
                rss_xml = self.template_renderer.render_rss_feed(posts)
                rss_path = self.build_dir / 'rss.xml'
                with open(rss_path, 'w', encoding='utf-8') as f:
                    f.write(rss_xml)
                rendering_stats['pages_rendered'] += 1
                rendering_stats['rendered_pages'].append('rss.xml')
                logger.info("Rendered RSS feed")

                self._report_progress(
                    BuildPhase.TEMPLATE_RENDERING,
                    "Rendered RSS feed",
                    100
                )
            except Exception as e:
                logger.error(f"Failed to render RSS feed: {e}")
                rendering_stats['rendering_errors'] += 1

            if rendering_stats['rendering_errors'] > 0:
                raise BuildGeneratingError(f"Template rendering had {rendering_stats['rendering_errors']} errors")

            logger.info(f"Template rendering completed: {rendering_stats['pages_rendered']} pages rendered")
            return rendering_stats

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise BuildGeneratingError(f"Template rendering failed: {e}") from e

    def _copy_assets(self) -> dict[str, Any]:
        """
        Copy all static assets to build directory.

        Returns:
            Dictionary with asset copying statistics

        Raises:
            BuildGeneratingError: If asset copying fails
        """
        try:
            self._report_progress(
                BuildPhase.ASSET_COPYING,
                "Starting asset copying",
                0
            )

            # Copy all assets using the asset manager
            copy_results = self.asset_manager.copy_all_assets()

            self._report_progress(
                BuildPhase.ASSET_COPYING,
                f"Copied {copy_results['total_successful']} assets",
                100,
                copy_results
            )

            logger.info(f"Asset copying completed: {copy_results['total_successful']} files copied")
            return copy_results

        except Exception as e:
            logger.error(f"Asset copying failed: {e}")
            raise BuildGeneratingError(f"Asset copying failed: {e}") from e

    def _verify_build_integrity(self) -> bool:
        """
        Verify the integrity of the generated build.

        Returns:
            True if build is valid, False otherwise
        """
        try:
            self._report_progress(
                BuildPhase.VERIFICATION,
                "Verifying build integrity",
                0
            )

            # Check if build directory exists
            if not self.build_dir.exists():
                logger.error("Build directory does not exist")
                return False

            # Check for required files
            required_files = ['index.html', 'archive.html', 'rss.xml']
            missing_files = []

            for file_name in required_files:
                file_path = self.build_dir / file_name
                if not file_path.exists():
                    missing_files.append(file_name)

            if missing_files:
                logger.error(f"Missing required files: {missing_files}")
                return False

            # Check if posts directory exists and has content
            posts_dir = self.build_dir / 'posts'
            if not posts_dir.exists():
                logger.warning("Posts directory does not exist")
            else:
                post_files = list(posts_dir.glob('*.html'))
                logger.info(f"Found {len(post_files)} post files in build")

            # Verify file sizes are reasonable
            for file_path in [self.build_dir / f for f in required_files]:
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    if file_size < 10:  # Very small files might indicate generation errors
                        logger.warning(f"File {file_path.name} is suspiciously small ({file_size} bytes)")

            self._report_progress(
                BuildPhase.VERIFICATION,
                "Build integrity verified",
                100
            )

            logger.info("Build integrity verification passed")
            return True

        except Exception as e:
            logger.error(f"Build integrity verification failed: {e}")
            return False

    def _cleanup_backup(self) -> bool:
        """
        Clean up backup directory after successful build.

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
                logger.info(f"Cleaned up backup directory: {self.backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup backup: {e}")
            return False

    def build(self) -> BuildResult:
        """
        Execute the complete build process with atomic operations.

        Returns:
            BuildResult with success status and detailed information
        """
        self.build_start_time = datetime.now()

        try:
            # Phase 1: Initialization and validation
            self._report_progress(
                BuildPhase.INITIALIZING,
                "Initializing build process",
                0
            )

            if not self._validate_build_preconditions():
                raise BuildGeneratingError("Build preconditions validation failed")

            # Phase 2: Create backup
            self._report_progress(
                BuildPhase.BACKUP_CREATION,
                "Creating backup of existing build",
                0
            )

            if not self._create_backup():
                raise BuildGeneratingError("Failed to create backup")

            # Phase 3: Process content
            self._report_progress(
                BuildPhase.CONTENT_PROCESSING,
                "Processing markdown content",
                0
            )

            processed_posts, content_stats = self._process_content()

            # Phase 4: Render templates
            self._report_progress(
                BuildPhase.TEMPLATE_RENDERING,
                "Rendering templates",
                0
            )

            rendering_stats = self._render_templates(processed_posts)

            # Phase 5: Copy assets
            self._report_progress(
                BuildPhase.ASSET_COPYING,
                "Copying static assets",
                0
            )

            asset_stats = self._copy_assets()

            # Phase 6: Verify build
            self._report_progress(
                BuildPhase.VERIFICATION,
                "Verifying build integrity",
                0
            )

            if not self._verify_build_integrity():
                raise BuildGeneratingError("Build integrity verification failed")

            # Phase 7: Cleanup
            self._report_progress(
                BuildPhase.CLEANUP,
                "Cleaning up backup",
                0
            )

            self._cleanup_backup()

            # Build completed successfully
            duration = (datetime.now() - self.build_start_time).total_seconds()

            self._report_progress(
                BuildPhase.COMPLETED,
                f"Build completed successfully in {duration:.1f}s",
                100
            )

            # Compile comprehensive stats
            build_stats = {
                'content': content_stats,
                'rendering': rendering_stats,
                'assets': asset_stats,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }

            return BuildResult(
                success=True,
                message=f"Build completed successfully in {duration:.1f} seconds",
                duration=duration,
                build_dir=self.build_dir,
                backup_dir=None,  # Backup was cleaned up
                progress_history=self.progress_history.copy(),
                stats=build_stats
            )

        except Exception as e:
            # Build failed - attempt rollback
            logger.error(f"Build failed: {e}")

            self._report_progress(
                BuildPhase.ROLLBACK,
                f"Build failed, attempting rollback: {e}",
                0
            )

            rollback_success = self._rollback_from_backup()

            duration = (datetime.now() - self.build_start_time).total_seconds() if self.build_start_time else 0

            if rollback_success:
                message = f"Build failed but rollback successful: {e}"
                self._report_progress(
                    BuildPhase.FAILED,
                    message,
                    0
                )
            else:
                message = f"Build failed and rollback failed: {e}"
                self._report_progress(
                    BuildPhase.FAILED,
                    message,
                    0
                )

            return BuildResult(
                success=False,
                message=message,
                duration=duration,
                build_dir=self.build_dir if rollback_success else None,
                backup_dir=self.backup_dir if not rollback_success else None,
                progress_history=self.progress_history.copy(),
                error=e
            )


# Global build generator instance
_build_generator: BuildGenerator | None = None


def get_build_generator(progress_callback: Callable[[BuildProgress], None] | None = None) -> BuildGenerator:
    """
    Get the global build generator instance.

    Args:
        progress_callback: Optional callback function for progress updates

    Returns:
        BuildGenerator instance
    """
    global _build_generator
    if _build_generator is None:
        _build_generator = BuildGenerator(progress_callback)
    return _build_generator


def build_site(progress_callback: Callable[[BuildProgress], None] | None = None) -> BuildResult:
    """
    Convenience function to build the site.

    Args:
        progress_callback: Optional callback function for progress updates

    Returns:
        BuildResult with success status and detailed information
    """
    generator = get_build_generator(progress_callback)
    return generator.build()
