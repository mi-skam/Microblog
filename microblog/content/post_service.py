"""
Post service for managing blog posts with markdown files and YAML frontmatter.

This module provides CRUD operations for blog posts stored as markdown files
with YAML frontmatter, including draft/publish workflow management.
"""

import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# No longer using Pydantic
from microblog.utils import ensure_directory, get_content_dir

from .validators import PostContent, validate_post_content

logger = logging.getLogger(__name__)


class PostNotFoundError(Exception):
    """Raised when a requested post cannot be found."""
    pass


class PostValidationError(Exception):
    """Raised when post validation fails."""
    pass


class PostFileError(Exception):
    """Raised when file operations fail."""
    pass


class PostService:
    """
    Service for managing blog posts with filesystem storage.

    Features:
    - CRUD operations for markdown posts with YAML frontmatter
    - Draft/publish status management
    - Slug-based and filename-based post retrieval
    - Batch operations for listing posts
    - File system safety and error handling
    """

    def __init__(self, posts_dir: Path | None = None):
        """
        Initialize the post service.

        Args:
            posts_dir: Directory for storing posts. Defaults to content/posts/
        """
        self.posts_dir = posts_dir or get_content_dir() / "posts"
        ensure_directory(self.posts_dir)
        logger.info(f"Post service initialized with directory: {self.posts_dir}")

    def create_post(
        self,
        title: str,
        content: str,
        date: date | None = None,
        slug: str | None = None,
        tags: list[str] | None = None,
        draft: bool = True,
        description: str | None = None
    ) -> PostContent:
        """
        Create a new blog post.

        Args:
            title: Post title
            content: Markdown content
            date: Publication date (defaults to today)
            slug: URL slug (auto-generated from title if not provided)
            tags: List of tags
            draft: Draft status (defaults to True)
            description: Post description/excerpt

        Returns:
            Created PostContent object

        Raises:
            PostValidationError: If post data is invalid
            PostFileError: If file creation fails
        """
        try:
            # Prepare frontmatter data
            frontmatter_data = {
                'title': title,
                'date': date or date.today(),
                'draft': draft
            }

            if slug:
                frontmatter_data['slug'] = slug
            if tags:
                frontmatter_data['tags'] = tags
            if description:
                frontmatter_data['description'] = description

            # Validate the post content
            post = validate_post_content(frontmatter_data, content)

            # Determine file path
            file_path = self.posts_dir / post.filename

            # Check if file already exists
            if file_path.exists():
                raise PostFileError(f"Post file already exists: {file_path}")

            # Save the post
            self._save_post_to_file(post, file_path)

            # Update the post with file path and timestamps
            if file_path.exists():
                stat = file_path.stat()
                from datetime import datetime
                post.file_path = str(file_path)
                post.created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                post.modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

            logger.info(f"Created new post: {post.frontmatter.title} ({file_path.name})")
            return post

        except ValueError as e:
            raise PostValidationError(f"Post validation failed: {e}") from e
        except Exception as e:
            raise PostFileError(f"Failed to create post: {e}") from e

    def get_post_by_slug(self, slug: str, include_drafts: bool = True) -> PostContent:
        """
        Retrieve a post by its slug.

        Args:
            slug: Post slug
            include_drafts: Whether to include draft posts

        Returns:
            PostContent object

        Raises:
            PostNotFoundError: If post is not found
            PostFileError: If file reading fails
        """
        # Find all markdown files and check their slugs
        for file_path in self.posts_dir.glob("*.md"):
            try:
                post = self._load_post_from_file(file_path)
                if post.computed_slug == slug:
                    if not include_drafts and post.is_draft:
                        continue
                    return post
            except Exception as e:
                logger.warning(f"Failed to load post {file_path}: {e}")
                continue

        raise PostNotFoundError(f"Post with slug '{slug}' not found")

    def get_post_by_filename(self, filename: str) -> PostContent:
        """
        Retrieve a post by its filename.

        Args:
            filename: Post filename (with .md extension)

        Returns:
            PostContent object

        Raises:
            PostNotFoundError: If post is not found
            PostFileError: If file reading fails
        """
        file_path = self.posts_dir / filename
        if not file_path.exists():
            raise PostNotFoundError(f"Post file not found: {filename}")

        try:
            return self._load_post_from_file(file_path)
        except Exception as e:
            raise PostFileError(f"Failed to load post {filename}: {e}") from e

    def update_post(
        self,
        slug: str,
        title: str | None = None,
        content: str | None = None,
        date: date | None = None,
        new_slug: str | None = None,
        tags: list[str] | None = None,
        draft: bool | None = None,
        description: str | None = None
    ) -> PostContent:
        """
        Update an existing post.

        Args:
            slug: Current slug of the post to update
            title: New title (optional)
            content: New content (optional)
            date: New date (optional)
            new_slug: New slug (optional)
            tags: New tags (optional)
            draft: New draft status (optional)
            description: New description (optional)

        Returns:
            Updated PostContent object

        Raises:
            PostNotFoundError: If post is not found
            PostValidationError: If updated data is invalid
            PostFileError: If file operations fail
        """
        try:
            # Get the existing post
            existing_post = self.get_post_by_slug(slug)
            old_file_path = Path(existing_post.file_path) if existing_post.file_path else None

            # Prepare updated frontmatter
            from dataclasses import asdict
            frontmatter_data = asdict(existing_post.frontmatter)

            if title is not None:
                frontmatter_data['title'] = title
            if date is not None:
                frontmatter_data['date'] = date
            if new_slug is not None:
                frontmatter_data['slug'] = new_slug
            if tags is not None:
                frontmatter_data['tags'] = tags
            if draft is not None:
                frontmatter_data['draft'] = draft
            if description is not None:
                frontmatter_data['description'] = description

            # Use existing content if not provided
            post_content = content if content is not None else existing_post.content

            # Convert date back to date object if it's a string
            if 'date' in frontmatter_data and isinstance(frontmatter_data['date'], str):
                from datetime import datetime
                frontmatter_data['date'] = datetime.fromisoformat(frontmatter_data['date']).date()

            # Validate the updated post
            updated_post = validate_post_content(frontmatter_data, post_content)

            # Determine new file path
            new_file_path = self.posts_dir / updated_post.filename

            # Save the updated post
            self._save_post_to_file(updated_post, new_file_path)

            # If filename changed, remove the old file
            if old_file_path and old_file_path != new_file_path and old_file_path.exists():
                old_file_path.unlink()
                logger.info(f"Removed old post file: {old_file_path.name}")

            # Update the post with file path and timestamps
            if new_file_path.exists():
                stat = new_file_path.stat()
                from datetime import datetime
                updated_post.file_path = str(new_file_path)
                updated_post.created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                updated_post.modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

            logger.info(f"Updated post: {updated_post.frontmatter.title} ({new_file_path.name})")
            return updated_post

        except PostNotFoundError:
            raise
        except ValueError as e:
            raise PostValidationError(f"Post validation failed: {e}") from e
        except Exception as e:
            raise PostFileError(f"Failed to update post: {e}") from e

    def delete_post(self, slug: str) -> bool:
        """
        Delete a post by slug.

        Args:
            slug: Post slug

        Returns:
            True if post was deleted, False if not found

        Raises:
            PostFileError: If file deletion fails
        """
        try:
            post = self.get_post_by_slug(slug)
            if post.file_path:
                file_path = Path(post.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted post: {post.frontmatter.title} ({file_path.name})")
                    return True
            return False
        except PostNotFoundError:
            return False
        except Exception as e:
            raise PostFileError(f"Failed to delete post: {e}") from e

    def list_posts(
        self,
        include_drafts: bool = False,
        tag_filter: str | None = None,
        limit: int | None = None
    ) -> list[PostContent]:
        """
        List posts with optional filtering.

        Args:
            include_drafts: Whether to include draft posts
            tag_filter: Filter by tag (case-insensitive)
            limit: Maximum number of posts to return

        Returns:
            List of PostContent objects, sorted by date (newest first)
        """
        posts = []

        for file_path in self.posts_dir.glob("*.md"):
            try:
                post = self._load_post_from_file(file_path)

                # Filter drafts
                if not include_drafts and post.is_draft:
                    continue

                # Filter by tag
                if tag_filter and tag_filter.lower() not in [tag.lower() for tag in post.frontmatter.tags]:
                    continue

                posts.append(post)

            except Exception as e:
                logger.warning(f"Failed to load post {file_path}: {e}")
                continue

        # Sort by date (newest first)
        posts.sort(key=lambda p: p.frontmatter.date, reverse=True)

        # Apply limit
        if limit and limit > 0:
            posts = posts[:limit]

        return posts

    def publish_post(self, slug: str) -> PostContent:
        """
        Publish a draft post (set draft=False).

        Args:
            slug: Post slug

        Returns:
            Updated PostContent object

        Raises:
            PostNotFoundError: If post is not found
            PostValidationError: If post is already published
        """
        post = self.get_post_by_slug(slug)
        if not post.is_draft:
            raise PostValidationError(f"Post '{slug}' is already published")

        return self.update_post(slug, draft=False)

    def unpublish_post(self, slug: str) -> PostContent:
        """
        Unpublish a post (set draft=True).

        Args:
            slug: Post slug

        Returns:
            Updated PostContent object

        Raises:
            PostNotFoundError: If post is not found
        """
        return self.update_post(slug, draft=True)

    def get_published_posts(self, tag_filter: str | None = None, limit: int | None = None) -> list[PostContent]:
        """
        Get only published posts.

        Args:
            tag_filter: Filter by tag (case-insensitive)
            limit: Maximum number of posts to return

        Returns:
            List of published PostContent objects, sorted by date (newest first)
        """
        return self.list_posts(include_drafts=False, tag_filter=tag_filter, limit=limit)

    def get_draft_posts(self, tag_filter: str | None = None, limit: int | None = None) -> list[PostContent]:
        """
        Get only draft posts.

        Args:
            tag_filter: Filter by tag (case-insensitive)
            limit: Maximum number of posts to return

        Returns:
            List of draft PostContent objects, sorted by date (newest first)
        """
        posts = self.list_posts(include_drafts=True, tag_filter=tag_filter, limit=limit)
        return [post for post in posts if post.is_draft]

    def _load_post_from_file(self, file_path: Path) -> PostContent:
        """
        Load a post from a markdown file with YAML frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            PostContent object

        Raises:
            PostFileError: If file reading or parsing fails
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                file_content = f.read()

            # Parse frontmatter and content
            frontmatter_data, content = self._parse_markdown_file(file_content)

            # Validate and create post
            post = validate_post_content(frontmatter_data, content, file_path)

            return post

        except FileNotFoundError as e:
            raise PostFileError(f"Post file not found: {file_path}") from e
        except Exception as e:
            raise PostFileError(f"Failed to load post from {file_path}: {e}") from e

    def _save_post_to_file(self, post: PostContent, file_path: Path) -> None:
        """
        Save a post to a markdown file with YAML frontmatter.

        Args:
            post: PostContent object to save
            file_path: Path where to save the file

        Raises:
            PostFileError: If file writing fails
        """
        try:
            # Ensure the posts directory exists
            ensure_directory(file_path.parent)

            # Convert frontmatter to dict and serialize
            from dataclasses import asdict
            frontmatter_dict = asdict(post.frontmatter)

            # Convert date to string for YAML serialization
            if 'date' in frontmatter_dict:
                frontmatter_dict['date'] = frontmatter_dict['date'].isoformat()

            # Create the complete file content
            frontmatter_yaml = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False)
            file_content = f"---\n{frontmatter_yaml}---\n\n{post.content}"

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

        except Exception as e:
            raise PostFileError(f"Failed to save post to {file_path}: {e}") from e

    def _parse_markdown_file(self, file_content: str) -> tuple[dict[str, Any], str]:
        """
        Parse markdown file with YAML frontmatter.

        Args:
            file_content: Raw file content

        Returns:
            Tuple of (frontmatter_dict, markdown_content)

        Raises:
            PostFileError: If parsing fails
        """
        try:
            # Match YAML frontmatter pattern
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
            match = re.match(frontmatter_pattern, file_content, re.DOTALL)

            if not match:
                raise PostFileError("Invalid markdown file format: missing YAML frontmatter")

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
            raise PostFileError(f"YAML parsing error in frontmatter: {e}") from e
        except Exception as e:
            raise PostFileError(f"Failed to parse markdown file: {e}") from e


# Global post service instance
_post_service: PostService | None = None


def get_post_service() -> PostService:
    """
    Get the global post service instance.

    Returns:
        PostService instance
    """
    global _post_service
    if _post_service is None:
        _post_service = PostService()
    return _post_service
