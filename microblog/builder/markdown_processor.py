"""
Markdown processor with python-markdown and pymdown-extensions.

This module provides markdown to HTML conversion with YAML frontmatter support,
syntax highlighting, and content validation for the static site generator.
"""

import logging
import re
from typing import Any

import markdown

from microblog.content.validators import PostContent, validate_post_content

logger = logging.getLogger(__name__)


class MarkdownProcessingError(Exception):
    """Raised when markdown processing fails."""
    pass


class MarkdownProcessor:
    """
    Markdown processor for converting blog posts to HTML.

    Features:
    - Syntax highlighting with pymdown-extensions
    - Table support
    - Table of contents generation
    - Content validation integration
    - Error handling and logging
    """

    def __init__(self):
        """Initialize the markdown processor with extensions."""
        self.markdown_instance = self._create_markdown_instance()
        logger.info("Markdown processor initialized")

    def _create_markdown_instance(self) -> markdown.Markdown:
        """
        Create a configured markdown instance with extensions.

        Returns:
            Configured markdown.Markdown instance
        """
        extensions = [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'pymdownx.superfences',
            'pymdownx.highlight',
            'pymdownx.inlinehilite',
            'pymdownx.magiclink',
            'pymdownx.betterem',
            'pymdownx.caret',
            'pymdownx.mark',
            'pymdownx.tilde',
            'pymdownx.smartsymbols',
        ]

        extension_configs = {
            'pymdownx.highlight': {
                'css_class': 'highlight',
                'guess_lang': True,
                'use_pygments': True,
            },
            'pymdownx.superfences': {
                'css_class': 'highlight',
            },
            'markdown.extensions.toc': {
                'permalink': True,
                'baselevel': 2,
            },
            'markdown.extensions.fenced_code': {
                'lang_prefix': 'language-',
            }
        }

        return markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )

    def process_content(self, post: PostContent) -> str:
        """
        Process markdown content to HTML.

        Args:
            post: PostContent object with markdown content

        Returns:
            Rendered HTML string

        Raises:
            MarkdownProcessingError: If processing fails
        """
        try:
            # Reset the markdown instance for clean processing
            self.markdown_instance.reset()

            # Convert markdown to HTML
            html_content = self.markdown_instance.convert(post.content)

            logger.debug(f"Processed markdown content for post: {post.frontmatter.title}")
            return html_content

        except Exception as e:
            raise MarkdownProcessingError(f"Failed to process markdown content: {e}") from e

    def process_markdown_text(self, markdown_text: str) -> str:
        """
        Process raw markdown text to HTML.

        Args:
            markdown_text: Raw markdown content

        Returns:
            Rendered HTML string

        Raises:
            MarkdownProcessingError: If processing fails
        """
        try:
            # Reset the markdown instance for clean processing
            self.markdown_instance.reset()

            # Convert markdown to HTML
            html_content = self.markdown_instance.convert(markdown_text)

            logger.debug("Processed raw markdown text")
            return html_content

        except Exception as e:
            raise MarkdownProcessingError(f"Failed to process markdown text: {e}") from e

    def process_file_content(self, file_content: str) -> tuple[dict[str, Any], str]:
        """
        Process complete markdown file with frontmatter.

        Args:
            file_content: Raw file content with YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, rendered_html)

        Raises:
            MarkdownProcessingError: If processing fails
        """
        try:
            # Parse frontmatter and content
            frontmatter_data, markdown_content = self._parse_frontmatter(file_content)

            # Process markdown to HTML
            html_content = self.process_markdown_text(markdown_content)

            logger.debug("Processed complete markdown file with frontmatter")
            return frontmatter_data, html_content

        except Exception as e:
            raise MarkdownProcessingError(f"Failed to process file content: {e}") from e

    def validate_and_process(self, frontmatter_data: dict[str, Any], content: str, file_path=None) -> tuple[PostContent, str]:
        """
        Validate post content and process markdown to HTML.

        Args:
            frontmatter_data: Frontmatter dictionary
            content: Markdown content
            file_path: Optional file path for validation

        Returns:
            Tuple of (validated_post, rendered_html)

        Raises:
            MarkdownProcessingError: If validation or processing fails
        """
        try:
            # Validate the post content first
            post = validate_post_content(frontmatter_data, content, file_path)

            # Process the markdown content
            html_content = self.process_content(post)

            logger.info(f"Validated and processed post: {post.frontmatter.title}")
            return post, html_content

        except ValueError as e:
            raise MarkdownProcessingError(f"Post validation failed: {e}") from e
        except Exception as e:
            raise MarkdownProcessingError(f"Failed to validate and process post: {e}") from e

    def _parse_frontmatter(self, file_content: str) -> tuple[dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown file content.

        Args:
            file_content: Raw file content

        Returns:
            Tuple of (frontmatter_dict, markdown_content)

        Raises:
            MarkdownProcessingError: If parsing fails
        """
        try:
            import yaml

            # Match YAML frontmatter pattern
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
            match = re.match(frontmatter_pattern, file_content, re.DOTALL)

            if not match:
                raise MarkdownProcessingError("Invalid markdown file format: missing YAML frontmatter")

            frontmatter_yaml = match.group(1)
            content = match.group(2)

            # Parse YAML frontmatter
            frontmatter_data = yaml.safe_load(frontmatter_yaml)
            if frontmatter_data is None:
                frontmatter_data = {}

            # Convert date string back to date object if needed
            if 'date' in frontmatter_data and isinstance(frontmatter_data['date'], str):
                from datetime import datetime
                frontmatter_data['date'] = datetime.fromisoformat(frontmatter_data['date']).date()

            return frontmatter_data, content

        except yaml.YAMLError as e:
            raise MarkdownProcessingError(f"YAML parsing error in frontmatter: {e}") from e
        except Exception as e:
            raise MarkdownProcessingError(f"Failed to parse frontmatter: {e}") from e

    def get_toc(self) -> str:
        """
        Get the table of contents from the last processed content.

        Returns:
            HTML table of contents string
        """
        if hasattr(self.markdown_instance, 'toc'):
            return self.markdown_instance.toc
        return ""

    def get_toc_tokens(self) -> list:
        """
        Get the table of contents tokens from the last processed content.

        Returns:
            List of TOC tokens
        """
        if hasattr(self.markdown_instance, 'toc_tokens'):
            return self.markdown_instance.toc_tokens
        return []


# Global markdown processor instance
_markdown_processor: MarkdownProcessor | None = None


def get_markdown_processor() -> MarkdownProcessor:
    """
    Get the global markdown processor instance.

    Returns:
        MarkdownProcessor instance
    """
    global _markdown_processor
    if _markdown_processor is None:
        _markdown_processor = MarkdownProcessor()
    return _markdown_processor