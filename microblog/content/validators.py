"""
Post validation models and utilities.

This module provides simple dataclass-based models for validating blog post frontmatter
and content, following the data model specification.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class PostFrontmatter:
    """
    Blog post frontmatter validation model.
    """
    title: str
    date: date
    slug: str = ""
    tags: list = field(default_factory=list)
    draft: bool = False
    description: str = ""

    def __post_init__(self):
        """Validate data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")

        self.title = self.title.strip()

        if len(self.title) > 200:
            raise ValueError("Title cannot be longer than 200 characters")

        if self.slug and len(self.slug) > 200:
            raise ValueError("Slug cannot be longer than 200 characters")

        if self.description and len(self.description) > 300:
            raise ValueError("Description cannot be longer than 300 characters")


@dataclass
class PostContent:
    """
    Blog post content model combining frontmatter and markdown content.
    """
    frontmatter: PostFrontmatter
    content: str
    file_path: str = ""
    created_at: str = ""
    modified_at: str = ""

    @property
    def is_draft(self) -> bool:
        """Check if this post is a draft."""
        return self.frontmatter.draft

    @property
    def is_published(self) -> bool:
        """Check if this post is published."""
        return not self.frontmatter.draft

    @property
    def computed_slug(self) -> str:
        """Get the slug, computing from title if not provided."""
        if self.frontmatter.slug:
            return self.frontmatter.slug

        # Generate slug from title
        slug = self.frontmatter.title.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        return slug or 'untitled'

    @property
    def filename(self) -> str:
        """Get the expected filename for this post."""
        date_str = self.frontmatter.date.strftime('%Y-%m-%d')
        return f"{date_str}-{self.computed_slug}.md"


def validate_frontmatter_dict(frontmatter_data: dict[str, Any]) -> PostFrontmatter:
    """
    Validate frontmatter data from a dictionary.
    """
    try:
        return PostFrontmatter(**frontmatter_data)
    except Exception as e:
        raise ValueError(f"Frontmatter validation failed: {e}") from e


def validate_post_content(frontmatter_data: dict[str, Any], content: str, file_path=None) -> PostContent:
    """
    Validate complete post content.
    """
    try:
        frontmatter = validate_frontmatter_dict(frontmatter_data)

        # Add file timestamps if file exists
        created_at = ""
        modified_at = ""
        file_path_str = ""

        if file_path and hasattr(file_path, 'exists') and file_path.exists():
            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            file_path_str = str(file_path)

        return PostContent(
            frontmatter=frontmatter,
            content=content,
            file_path=file_path_str,
            created_at=created_at,
            modified_at=modified_at
        )
    except Exception as e:
        raise ValueError(f"Post validation failed: {e}") from e
