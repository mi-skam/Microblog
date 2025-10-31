"""
Template rendering system with Jinja2 engine and context management.

This module provides template rendering functionality for the static site generator,
including template inheritance, context management, and RSS feed generation.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from microblog.content.post_service import PostContent, get_post_service
from microblog.server.config import get_config
from microblog.utils import get_templates_dir
from microblog.utils.cache import PerformanceTimer, get_template_cache

logger = logging.getLogger(__name__)


class TemplateRenderingError(Exception):
    """Raised when template rendering fails."""
    pass


class TemplateRenderer:
    """
    Template rendering engine with Jinja2 and context management.

    Features:
    - Jinja2 template engine with inheritance support
    - Site-wide context management
    - RSS feed generation
    - Template validation and error handling
    - Template caching and performance optimization
    """

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the template renderer.

        Args:
            templates_dir: Directory containing templates. Defaults to project templates/
        """
        self.templates_dir = templates_dir or get_templates_dir()
        self.env = self._create_jinja_environment()
        self.config = get_config()
        self.post_service = get_post_service()
        self.template_cache = get_template_cache()
        logger.info(f"Template renderer initialized with directory: {self.templates_dir}")

    def _create_jinja_environment(self) -> Environment:
        """
        Create and configure the Jinja2 environment.

        Returns:
            Configured Jinja2 Environment
        """
        loader = FileSystemLoader(str(self.templates_dir))
        env = Environment(
            loader=loader,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        env.filters['dateformat'] = self._format_date
        env.filters['rfc2822'] = self._format_rfc2822
        env.filters['excerpt'] = self._create_excerpt

        # Add custom globals
        env.globals['now'] = datetime.now
        env.globals['current_year'] = datetime.now().year

        return env

    def _format_date(self, date_obj, format_str: str = '%B %d, %Y') -> str:
        """
        Format a date object for display.

        Args:
            date_obj: Date or datetime object
            format_str: strftime format string

        Returns:
            Formatted date string
        """
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_str)
        return str(date_obj)

    def _format_rfc2822(self, date_obj) -> str:
        """
        Format a date for RSS feeds (RFC 2822 format).

        Args:
            date_obj: Date or datetime object

        Returns:
            RFC 2822 formatted date string
        """
        if hasattr(date_obj, 'strftime'):
            # Convert date to datetime if needed
            if not hasattr(date_obj, 'hour'):
                from datetime import datetime, time
                date_obj = datetime.combine(date_obj, time())
            return date_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
        return str(date_obj)

    def _create_excerpt(self, content: str, length: int = 150) -> str:
        """
        Create an excerpt from content.

        Args:
            content: Source content
            length: Maximum excerpt length

        Returns:
            Truncated excerpt with ellipsis
        """
        import re
        # Remove HTML tags for plain text excerpt
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        # Normalize whitespace
        clean_content = ' '.join(clean_content.split())

        if len(clean_content) <= length:
            return clean_content

        # Find the last word boundary before the limit
        truncated = clean_content[:length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]

        return truncated + '...'

    def _get_base_context(self) -> dict[str, Any]:
        """
        Get the base template context with site configuration.

        Returns:
            Dictionary with base template context
        """
        return {
            'site': {
                'title': self.config.site.title,
                'url': self.config.site.url,
                'author': self.config.site.author,
                'description': self.config.site.description,
            },
            'build': {
                'posts_per_page': self.config.build.posts_per_page,
            },
            'current_year': datetime.now().year,
        }

    def render_template(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Additional context variables

        Returns:
            Rendered HTML string

        Raises:
            TemplateRenderingError: If template rendering fails
        """
        try:
            with PerformanceTimer(f"template_render_{template_name}"):
                # Check cache for rendered output first
                cached_output = self.template_cache.get_rendered_output(template_name, context)
                if cached_output is not None:
                    logger.debug(f"Template cache hit: {template_name}")
                    return cached_output

                # Get compiled template (may be cached)
                template_path = self.templates_dir / template_name
                template = self.template_cache.get_compiled_template(
                    template_path,
                    lambda: self.env.get_template(template_name)
                )

                # Merge base context with provided context
                render_context = self._get_base_context()
                if context:
                    render_context.update(context)

                # Render template
                result = template.render(render_context)

                # Cache the rendered output
                self.template_cache.put_rendered_output(template_name, context, result)

                logger.debug(f"Rendered and cached template: {template_name}")
                return result

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render template '{template_name}': {e}") from e

    def render_homepage(self, posts: list[PostContent] | None = None, page: int = 1) -> str:
        """
        Render the homepage with recent posts.

        Args:
            posts: List of posts to display. Defaults to published posts
            page: Page number for pagination

        Returns:
            Rendered homepage HTML

        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            if posts is None:
                posts = self.post_service.get_published_posts(limit=self.config.build.posts_per_page)

            context = {
                'posts': posts,
                'page': page,
                'page_type': 'homepage',
            }

            return self.render_template('index.html', context)

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render homepage: {e}") from e

    def render_post(self, post: PostContent, html_content: str) -> str:
        """
        Render a single post page.

        Args:
            post: Post content object
            html_content: Rendered markdown content

        Returns:
            Rendered post page HTML

        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            context = {
                'post': post,
                'content': html_content,
                'page_type': 'post',
            }

            return self.render_template('post.html', context)

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render post '{post.frontmatter.title}': {e}") from e

    def render_archive(self, posts: list[PostContent] | None = None) -> str:
        """
        Render the archive page with all posts.

        Args:
            posts: List of posts to display. Defaults to all published posts

        Returns:
            Rendered archive page HTML

        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            if posts is None:
                posts = self.post_service.get_published_posts()

            # Group posts by year for archive display
            posts_by_year = {}
            for post in posts:
                year = post.frontmatter.date.year
                if year not in posts_by_year:
                    posts_by_year[year] = []
                posts_by_year[year].append(post)

            context = {
                'posts': posts,
                'posts_by_year': posts_by_year,
                'page_type': 'archive',
            }

            return self.render_template('archive.html', context)

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render archive: {e}") from e

    def render_tag_page(self, tag: str, posts: list[PostContent] | None = None) -> str:
        """
        Render a tag page with posts filtered by tag.

        Args:
            tag: Tag to filter by
            posts: List of posts with the tag. Defaults to auto-filtered posts

        Returns:
            Rendered tag page HTML

        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            if posts is None:
                posts = self.post_service.get_published_posts(tag_filter=tag)

            context = {
                'tag': tag,
                'posts': posts,
                'page_type': 'tag',
            }

            return self.render_template('tag.html', context)

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render tag page '{tag}': {e}") from e

    def render_rss_feed(self, posts: list[PostContent] | None = None) -> str:
        """
        Render RSS feed XML.

        Args:
            posts: List of posts for the feed. Defaults to recent published posts

        Returns:
            Rendered RSS XML

        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            if posts is None:
                posts = self.post_service.get_published_posts(limit=20)

            # Ensure posts have proper datetime for RSS
            from datetime import datetime, time
            processed_posts = []
            for post in posts:
                # Create a copy and ensure datetime
                post_data = {
                    'frontmatter': post.frontmatter,
                    'content': post.content,
                    'computed_slug': post.computed_slug,
                    'is_draft': post.is_draft,
                }

                # Convert date to datetime if needed
                if hasattr(post.frontmatter.date, 'hour'):
                    post_data['pub_date'] = post.frontmatter.date
                else:
                    post_data['pub_date'] = datetime.combine(post.frontmatter.date, time())

                processed_posts.append(post_data)

            context = {
                'posts': processed_posts,
                'build_date': datetime.now(),
                'page_type': 'rss',
            }

            return self.render_template('rss.xml', context)

        except Exception as e:
            raise TemplateRenderingError(f"Failed to render RSS feed: {e}") from e

    def get_all_tags(self) -> list[str]:
        """
        Get all unique tags from published posts.

        Returns:
            Sorted list of unique tags
        """
        try:
            posts = self.post_service.get_published_posts()
            all_tags = set()

            for post in posts:
                all_tags.update(tag.lower() for tag in post.frontmatter.tags)

            return sorted(all_tags)

        except Exception as e:
            logger.error(f"Failed to get all tags: {e}")
            return []

    def validate_template(self, template_name: str) -> tuple[bool, str | None]:
        """
        Validate that a template exists and can be loaded.

        Args:
            template_name: Name of the template to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.env.get_template(template_name)
            return True, None
        except Exception as e:
            return False, str(e)

    def clear_template_cache(self):
        """Clear all template caches."""
        self.template_cache.clear_all()
        logger.info("Template cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get template cache statistics."""
        return self.template_cache.get_stats()

    def invalidate_template_cache(self, template_name: str):
        """Invalidate cache for a specific template."""
        self.template_cache.invalidate_template(template_name)
        logger.debug(f"Invalidated cache for template: {template_name}")


# Global template renderer instance
_template_renderer: TemplateRenderer | None = None


def get_template_renderer() -> TemplateRenderer:
    """
    Get the global template renderer instance.

    Returns:
        TemplateRenderer instance
    """
    global _template_renderer
    if _template_renderer is None:
        _template_renderer = TemplateRenderer()
    return _template_renderer
