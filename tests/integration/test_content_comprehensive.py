"""
Comprehensive integration tests for content management system.

This module provides extensive coverage for content management including
post services, validators, and content operations.
"""

import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from microblog.content.post_service import (
    PostFileError,
    PostNotFoundError,
    PostService,
    PostValidationError,
)
from microblog.content.validators import (
    PostContent,
    PostFrontmatter,
    validate_frontmatter_dict,
    validate_post_content,
)


class TestContentManagementComprehensive:
    """Comprehensive tests for content management system."""

    @pytest.fixture
    def temp_content_dir(self):
        """Create temporary content directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = Path(temp_dir)
            posts_dir = content_dir / "posts"
            posts_dir.mkdir(parents=True)
            yield content_dir

    @pytest.fixture
    def post_service(self, temp_content_dir):
        """Create PostService instance with temporary directory."""
        posts_dir = temp_content_dir / "posts"
        return PostService(posts_dir=posts_dir)

    def test_post_service_creation_operations(self, post_service):
        """Test post creation operations in PostService."""
        # Test successful post creation
        post = post_service.create_post(
            title="Test Post",
            content="# Test Content\n\nThis is a test post.",
            tags=["test", "blog"],
            draft=False
        )

        assert post is not None
        assert post.frontmatter.title == "Test Post"
        assert post.content == "# Test Content\n\nThis is a test post."
        assert post.frontmatter.tags == ["test", "blog"]
        assert post.is_draft is False
        assert post.computed_slug == "test-post"

        # Test post file was created
        post_file = post_service.posts_dir / f"{post.computed_slug}.md"
        assert post_file.exists()

        # Test post creation with draft
        draft_post = post_service.create_post(
            title="Draft Post",
            content="Draft content",
            draft=True
        )

        assert draft_post.is_draft is True

    def test_post_service_retrieval_operations(self, post_service):
        """Test post retrieval operations in PostService."""
        # Create test posts
        post1 = post_service.create_post(
            title="Published Post",
            content="Published content",
            draft=False
        )
        post2 = post_service.create_post(
            title="Draft Post",
            content="Draft content",
            draft=True
        )

        # Test list all posts
        all_posts = post_service.list_posts()
        assert len(all_posts) == 2

        # Test get published posts
        published_posts = post_service.get_published_posts()
        assert len(published_posts) == 1
        assert published_posts[0].frontmatter.title == "Published Post"

        # Test get draft posts
        draft_posts = post_service.get_draft_posts()
        assert len(draft_posts) == 1
        assert draft_posts[0].frontmatter.title == "Draft Post"

        # Test get post by slug
        retrieved_post = post_service.get_post_by_slug(post1.computed_slug)
        assert retrieved_post is not None
        assert retrieved_post.frontmatter.title == "Published Post"

        # Test get non-existent post
        try:
            post_service.get_post_by_slug("non-existent")
            assert False, "Should have raised PostNotFoundError"
        except PostNotFoundError:
            pass

    def test_post_service_update_operations(self, post_service):
        """Test post update operations in PostService."""
        # Create initial post
        post = post_service.create_post(
            title="Original Title",
            content="Original content",
            tags=["original"],
            draft=True
        )

        original_slug = post.computed_slug

        # Test update post
        updated_post = post_service.update_post(
            slug=original_slug,
            title="Updated Title",
            content="Updated content",
            tags=["updated", "modified"],
            draft=False
        )

        assert updated_post.frontmatter.title == "Updated Title"
        assert updated_post.content == "Updated content"
        assert updated_post.frontmatter.tags == ["updated", "modified"]
        assert updated_post.is_draft is False

        # Test update non-existent post
        try:
            post_service.update_post(
                slug="non-existent",
                title="New Title",
                content="New content"
            )
            assert False, "Should have raised PostNotFoundError"
        except PostNotFoundError:
            pass

    def test_post_service_deletion_operations(self, post_service):
        """Test post deletion operations in PostService."""
        # Create test post
        post = post_service.create_post(
            title="Post to Delete",
            content="Content to delete"
        )

        post_slug = post.computed_slug
        post_file = post_service.posts_dir / f"{post_slug}.md"

        # Verify post exists
        assert post_file.exists()
        assert post_service.get_post_by_slug(post_slug) is not None

        # Delete post
        post_service.delete_post(post_slug)

        # Verify post is deleted
        assert not post_file.exists()
        try:
            post_service.get_post_by_slug(post_slug)
            assert False, "Should have raised PostNotFoundError"
        except PostNotFoundError:
            pass

        # Test delete non-existent post
        try:
            post_service.delete_post("non-existent")
            assert False, "Should have raised PostNotFoundError"
        except PostNotFoundError:
            pass

    def test_frontmatter_validation_comprehensive(self):
        """Test comprehensive frontmatter validation scenarios."""
        # Test valid frontmatter
        valid_frontmatter_data = {
            "title": "Valid Title",
            "date": date.today(),
            "tags": ["tag1", "tag2"],
            "draft": False
        }

        try:
            frontmatter = validate_frontmatter_dict(valid_frontmatter_data)
            assert frontmatter.title == "Valid Title"
            assert frontmatter.tags == ["tag1", "tag2"]
        except ValueError:
            assert False, "Should not raise error for valid frontmatter"

        # Test minimal valid frontmatter
        minimal_frontmatter_data = {"title": "Title", "date": date.today()}
        try:
            frontmatter = validate_frontmatter_dict(minimal_frontmatter_data)
            assert frontmatter.title == "Title"
        except ValueError:
            assert False, "Should not raise error for minimal valid frontmatter"

        # Test invalid frontmatter
        try:
            validate_frontmatter_dict({})  # Missing title
            assert False, "Should raise error for missing title"
        except ValueError:
            pass

        try:
            validate_frontmatter_dict({"title": ""})  # Empty title
            assert False, "Should raise error for empty title"
        except ValueError:
            pass

    def test_post_content_validation_comprehensive(self):
        """Test comprehensive post content validation."""
        # Test valid post content
        valid_frontmatter_data = {
            "title": "Valid Post",
            "date": date.today(),
            "tags": ["test"],
            "draft": False
        }
        valid_content = "# Valid Post\n\nThis is valid content."

        try:
            post = validate_post_content(valid_frontmatter_data, valid_content)
            assert post.frontmatter.title == "Valid Post"
            assert post.content == valid_content
        except ValueError:
            assert False, "Should not raise error for valid post"

        # Test post with invalid frontmatter
        try:
            validate_post_content({"title": ""}, "content")
            assert False, "Should raise error for invalid frontmatter"
        except ValueError:
            pass

    def test_post_model_functionality(self):
        """Test PostContent and PostFrontmatter model functionality."""
        # Test PostFrontmatter creation
        frontmatter = PostFrontmatter(
            title="Test Post",
            date=date.today(),
            tags=["test", "blog"],
            draft=False
        )

        assert frontmatter.title == "Test Post"
        assert frontmatter.tags == ["test", "blog"]
        assert frontmatter.draft is False

        # Test PostContent creation
        post = PostContent(
            frontmatter=frontmatter,
            content="# Test Content"
        )

        assert post.frontmatter.title == "Test Post"
        assert post.content == "# Test Content"
        assert post.is_draft is False
        assert post.is_published is True
        assert post.computed_slug == "test-post"

    def test_post_service_error_scenarios(self, post_service):
        """Test PostService error handling scenarios."""
        # Test creation with invalid data
        try:
            post_service.create_post(
                title="",  # Invalid title
                content="Content"
            )
            assert False, "Should raise PostValidationError"
        except PostValidationError:
            pass

        # Test file system errors (mock)
        with patch('pathlib.Path.write_text', side_effect=OSError("Permission denied")):
            try:
                post_service.create_post(
                    title="Test Post",
                    content="Test content"
                )
                assert False, "Should raise PostFileError"
            except PostFileError:
                pass

    def test_post_service_slug_generation(self, post_service):
        """Test slug generation and conflict resolution."""
        # Create post with specific title
        post1 = post_service.create_post(
            title="Test Post",
            content="First post"
        )
        assert post1.computed_slug == "test-post"

        # Create another post with same title
        post2 = post_service.create_post(
            title="Test Post",
            content="Second post"
        )
        # Should generate unique slug
        assert post2.computed_slug != post1.computed_slug
        assert "test-post" in post2.computed_slug

    def test_post_service_date_handling(self, post_service):
        """Test date handling in post operations."""
        # Test post creation with current date
        post = post_service.create_post(
            title="Dated Post",
            content="Content with date"
        )

        assert post.frontmatter.date is not None
        assert isinstance(post.frontmatter.date, date)
        assert post.frontmatter.date == date.today()

        # Test update preserves date
        updated_post = post_service.update_post(
            slug=post.computed_slug,
            title="Updated Title",
            content="Updated content"
        )

        assert updated_post.frontmatter.date == post.frontmatter.date

    def test_post_service_tag_processing(self, post_service):
        """Test tag processing and normalization."""
        # Test tag normalization
        post = post_service.create_post(
            title="Tagged Post",
            content="Content with tags",
            tags=["Tag1", "tag-2", "TAG_3"]  # Mixed case and formats
        )

        # Tags should be normalized (lowercase, hyphens)
        assert all(tag.islower() for tag in post.frontmatter.tags)
        assert all("-" not in tag or "_" not in tag for tag in post.frontmatter.tags)

    def test_post_service_content_processing(self, post_service):
        """Test content processing and markdown handling."""
        # Test with various markdown content
        markdown_content = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Subsection

- List item 1
- List item 2

```python
def hello():
    print("Hello, World!")
```

[Link text](https://example.com)
"""

        post = post_service.create_post(
            title="Markdown Post",
            content=markdown_content
        )

        assert post.content == markdown_content
        # Content should be preserved as-is

    def test_post_service_filtering_operations(self, post_service):
        """Test post filtering and search operations."""
        # Create posts with different characteristics
        post_service.create_post(
            title="Python Tutorial",
            content="Learn Python programming",
            tags=["python", "tutorial"],
            draft=False
        )

        post_service.create_post(
            title="JavaScript Guide",
            content="Learn JavaScript programming",
            tags=["javascript", "guide"],
            draft=False
        )

        post_service.create_post(
            title="Draft Article",
            content="This is a draft",
            tags=["draft"],
            draft=True
        )

        # Test filtering by draft status
        published = post_service.get_published_posts()
        drafts = post_service.get_draft_posts()

        assert len(published) == 2
        assert len(drafts) == 1

        # Test getting all posts
        all_posts = post_service.list_posts()
        assert len(all_posts) == 3

    def test_post_service_file_system_integration(self, post_service):
        """Test file system integration and file handling."""
        # Test post file creation
        post = post_service.create_post(
            title="File System Test",
            content="Testing file operations"
        )

        post_file = post_service.posts_dir / f"{post.computed_slug}.md"
        assert post_file.exists()

        # Read file content and verify format
        file_content = post_file.read_text(encoding="utf-8")
        assert "---" in file_content  # YAML frontmatter delimiters
        assert "title: File System Test" in file_content
        assert "Testing file operations" in file_content

    def test_frontmatter_edge_cases(self):
        """Test PostFrontmatter edge cases and validation."""
        # Test empty title
        try:
            PostFrontmatter(title="", date=date.today())
            assert False, "Should raise error for empty title"
        except ValueError:
            pass

        # Test very long title
        try:
            PostFrontmatter(title="a" * 300, date=date.today())
            assert False, "Should raise error for too long title"
        except ValueError:
            pass

        # Test very long description
        try:
            PostFrontmatter(
                title="Valid Title",
                date=date.today(),
                description="a" * 400
            )
            assert False, "Should raise error for too long description"
        except ValueError:
            pass

    def test_post_service_concurrent_operations(self, post_service):
        """Test post service handling of concurrent-like operations."""
        # Simulate concurrent post creation with same title
        posts = []
        for i in range(3):
            post = post_service.create_post(
                title="Concurrent Post",
                content=f"Content {i}"
            )
            posts.append(post)

        # All posts should have unique slugs
        slugs = [post.computed_slug for post in posts]
        assert len(set(slugs)) == len(slugs)  # All unique

    def test_post_service_large_content_handling(self, post_service):
        """Test handling of large content files."""
        # Create post with large content
        large_content = "# Large Post\n\n" + "Lorem ipsum " * 10000

        post = post_service.create_post(
            title="Large Content Post",
            content=large_content
        )

        assert post.content == large_content

        # Verify file was written correctly
        retrieved_post = post_service.get_post_by_slug(post.computed_slug)
        assert retrieved_post.content == large_content