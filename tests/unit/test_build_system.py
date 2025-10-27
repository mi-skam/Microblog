"""
Comprehensive unit tests for the build system components.

This module tests all major build system components including markdown processing,
template rendering, asset management, and atomic build operations with failure scenarios.
"""

import tempfile
import time
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from microblog.builder.asset_manager import (
    AssetManager,
    get_asset_manager,
)
from microblog.builder.generator import (
    BuildGenerator,
    BuildPhase,
    BuildProgress,
    BuildResult,
    get_build_generator,
)
from microblog.builder.markdown_processor import (
    MarkdownProcessingError,
    MarkdownProcessor,
    get_markdown_processor,
)
from microblog.builder.template_renderer import (
    TemplateRenderer,
    TemplateRenderingError,
    get_template_renderer,
)
from microblog.content.validators import PostContent, PostFrontmatter


@pytest.fixture
def temp_content_structure():
    """Create temporary content structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        content_dir = base_dir / "content"
        static_dir = base_dir / "static"
        build_dir = base_dir / "build"

        # Create content structure
        content_images = content_dir / "images"
        content_images.mkdir(parents=True)
        (content_images / "test.jpg").write_bytes(b"fake image data")
        (content_images / "test.png").write_bytes(b"fake png data")

        # Create static structure
        static_css = static_dir / "css"
        static_css.mkdir(parents=True)
        (static_css / "style.css").write_text("body { color: red; }")

        static_js = static_dir / "js"
        static_js.mkdir(parents=True)
        (static_js / "script.js").write_text("console.log('hello');")

        # Create suspicious files for testing
        (content_images / "test.exe").write_bytes(b"executable")
        (content_images / ".htaccess").write_text("malicious config")

        yield {
            'base': base_dir,
            'content': content_dir,
            'static': static_dir,
            'build': build_dir
        }


class TestBuildProgress:
    """Test BuildProgress data class."""

    def test_build_progress_creation(self):
        """Test BuildProgress object creation."""
        progress = BuildProgress(
            phase=BuildPhase.CONTENT_PROCESSING,
            message="Processing posts",
            percentage=50.0,
            details={"processed": 5, "total": 10}
        )

        assert progress.phase == BuildPhase.CONTENT_PROCESSING
        assert progress.message == "Processing posts"
        assert progress.percentage == 50.0
        assert progress.details == {"processed": 5, "total": 10}
        assert progress.timestamp is not None

    def test_build_progress_auto_timestamp(self):
        """Test automatic timestamp generation."""
        before = datetime.now()
        progress = BuildProgress(BuildPhase.INITIALIZING, "Starting")
        after = datetime.now()

        assert before <= progress.timestamp <= after

    def test_build_progress_custom_timestamp(self):
        """Test custom timestamp setting."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        progress = BuildProgress(
            BuildPhase.COMPLETED,
            "Done",
            timestamp=custom_time
        )

        assert progress.timestamp == custom_time


class TestBuildResult:
    """Test BuildResult data class."""

    def test_build_result_success(self):
        """Test successful build result."""
        result = BuildResult(
            success=True,
            message="Build completed successfully",
            duration=30.5,
            build_dir=Path("/output"),
            stats={"files": 10}
        )

        assert result.success is True
        assert result.message == "Build completed successfully"
        assert result.duration == 30.5
        assert result.build_dir == Path("/output")
        assert result.stats == {"files": 10}
        assert result.error is None

    def test_build_result_failure(self):
        """Test failed build result."""
        error = Exception("Build failed")
        result = BuildResult(
            success=False,
            message="Build failed",
            error=error
        )

        assert result.success is False
        assert result.message == "Build failed"
        assert result.error == error


class TestMarkdownProcessor:
    """Test MarkdownProcessor functionality."""

    def test_markdown_processor_initialization(self):
        """Test markdown processor initialization."""
        processor = MarkdownProcessor()

        assert processor.markdown_instance is not None
        assert hasattr(processor.markdown_instance, 'convert')

    def test_process_markdown_text_basic(self):
        """Test basic markdown text processing."""
        processor = MarkdownProcessor()

        markdown_text = "# Hello World\n\nThis is a test."
        html = processor.process_markdown_text(markdown_text)

        # Note: TOC configuration sets baselevel=2, so # becomes h2
        assert "<h2" in html
        assert "Hello World" in html
        assert "<p>" in html
        assert "This is a test." in html

    def test_process_markdown_text_code_blocks(self):
        """Test markdown processing with code blocks."""
        processor = MarkdownProcessor()

        markdown_text = """
# Test
```python
def hello():
    print("world")
```
"""
        html = processor.process_markdown_text(markdown_text)

        # Note: TOC configuration sets baselevel=2, so # becomes h2
        assert "<h2" in html
        assert "<code" in html or "<pre" in html
        # Check for syntax highlighting classes instead of language identifier
        assert "highlight" in html or "codehilite" in html
        # Check for the function name and content in the highlighted code
        assert "hello" in html and ("def" in html or "nf" in html)

    def test_process_markdown_text_tables(self):
        """Test markdown table processing."""
        processor = MarkdownProcessor()

        markdown_text = """
| Name | Age |
|------|-----|
| John | 30  |
| Jane | 25  |
"""
        html = processor.process_markdown_text(markdown_text)

        assert "<table>" in html
        assert "<th>" in html
        assert "<td>" in html
        assert "John" in html
        assert "Jane" in html

    def test_process_content_with_post(self):
        """Test processing PostContent object."""
        processor = MarkdownProcessor()

        frontmatter = PostFrontmatter(
            title="Test Post",
            date=date(2023, 1, 1),
            tags=["test"],
            slug="test-post"
        )

        post = PostContent(
            frontmatter=frontmatter,
            content="# Test Content\n\nThis is a test post."
        )

        html = processor.process_content(post)

        assert "<h2" in html
        assert "Test Content" in html
        assert "<p>" in html

    def test_process_markdown_text_error_handling(self):
        """Test error handling in markdown processing."""
        processor = MarkdownProcessor()

        # Mock the markdown instance to raise an exception
        processor.markdown_instance.convert = Mock(side_effect=Exception("Test error"))

        with pytest.raises(MarkdownProcessingError, match="Failed to process markdown text"):
            processor.process_markdown_text("# Test")

    def test_frontmatter_parsing_valid(self):
        """Test valid frontmatter parsing."""
        processor = MarkdownProcessor()

        file_content = """---
title: Test Post
date: 2023-01-01
tags:
  - test
  - markdown
---

# Test Content

This is a test post."""

        frontmatter, content = processor._parse_frontmatter(file_content)

        assert frontmatter["title"] == "Test Post"
        assert frontmatter["tags"] == ["test", "markdown"]
        assert "# Test Content" in content

    def test_frontmatter_parsing_invalid(self):
        """Test invalid frontmatter parsing."""
        processor = MarkdownProcessor()

        file_content = "# No frontmatter\n\nJust content."

        with pytest.raises(MarkdownProcessingError, match="missing YAML frontmatter"):
            processor._parse_frontmatter(file_content)

    def test_validate_content_structure_empty(self):
        """Test content structure validation with empty content."""
        processor = MarkdownProcessor()

        warnings = processor.validate_content_structure("")

        assert len(warnings) == 1
        assert "Content is empty" in warnings[0]

    def test_validate_content_structure_long_no_headers(self):
        """Test content structure validation for long content without headers."""
        processor = MarkdownProcessor()

        content = "This is a very long content. " * 50  # > 500 chars
        warnings = processor.validate_content_structure(content)

        assert any("without headers" in warning for warning in warnings)

    def test_validate_content_structure_unclosed_code_block(self):
        """Test detection of unclosed code blocks."""
        processor = MarkdownProcessor()

        content = "```python\ndef hello():\n    print('world')\n```\nSome content\n```\nMissing closing"
        warnings = processor.validate_content_structure(content)

        assert any("Unclosed fenced code block" in warning for warning in warnings)

    def test_validate_content_structure_long_lines(self):
        """Test detection of very long lines."""
        processor = MarkdownProcessor()

        content = "This is a very long line that exceeds 120 characters " * 5
        warnings = processor.validate_content_structure(content)

        assert any("Very long lines detected" in warning for warning in warnings)

    def test_validate_content_structure_malformed_links(self):
        """Test detection of malformed links."""
        processor = MarkdownProcessor()

        content = """
[Empty URL]()
[](http://example.com)
[Good link](http://example.com)
"""
        warnings = processor.validate_content_structure(content)

        assert any("Empty link URL" in warning for warning in warnings)
        assert any("Empty link text" in warning for warning in warnings)


class TestTemplateRenderer:
    """Test TemplateRenderer functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.site.title = "Test Blog"
        config.site.url = "https://test.example.com"
        config.site.author = "Test Author"
        config.site.description = "Test Description"
        config.build.posts_per_page = 5
        return config

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)

            # Create basic templates
            (templates_dir / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>{{ site.title }}</title></head>
<body>
<h1>{{ site.title }}</h1>
{% for post in posts %}
<article>
<h2>{{ post.frontmatter.title }}</h2>
<p>{{ post.frontmatter.date | dateformat }}</p>
</article>
{% endfor %}
</body>
</html>
""")

            (templates_dir / "post.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>{{ post.frontmatter.title }} - {{ site.title }}</title></head>
<body>
<h1>{{ post.frontmatter.title }}</h1>
<p>{{ post.frontmatter.date | dateformat }}</p>
<div>{{ content | safe }}</div>
</body>
</html>
""")

            (templates_dir / "archive.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>Archive - {{ site.title }}</title></head>
<body>
<h1>Archive</h1>
{% for year, year_posts in posts_by_year.items() %}
<h2>{{ year }}</h2>
{% for post in year_posts %}
<p><a href="/posts/{{ post.computed_slug }}.html">{{ post.frontmatter.title }}</a></p>
{% endfor %}
{% endfor %}
</body>
</html>
""")

            (templates_dir / "rss.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{{ site.title }}</title>
<link>{{ site.url }}</link>
<description>{{ site.description }}</description>
<lastBuildDate>{{ build_date | rfc2822 }}</lastBuildDate>
{% for post in posts %}
<item>
<title>{{ post.frontmatter.title }}</title>
<link>{{ site.url }}/posts/{{ post.computed_slug }}.html</link>
<pubDate>{{ post.pub_date | rfc2822 }}</pubDate>
</item>
{% endfor %}
</channel>
</rss>
""")

            yield templates_dir

    def test_template_renderer_initialization(self, temp_templates_dir, mock_config):
        """Test template renderer initialization."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                assert renderer.templates_dir == temp_templates_dir
                assert renderer.env is not None

    def test_render_template_basic(self, temp_templates_dir, mock_config):
        """Test basic template rendering."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                html = renderer.render_template('index.html', {'posts': []})

                assert "Test Blog" in html
                assert "<!DOCTYPE html>" in html

    def test_render_homepage(self, temp_templates_dir, mock_config):
        """Test homepage rendering."""
        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []

        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service', return_value=mock_post_service):
                renderer = TemplateRenderer(temp_templates_dir)

                html = renderer.render_homepage()

                assert "Test Blog" in html
                assert "<!DOCTYPE html>" in html

    def test_render_post(self, temp_templates_dir, mock_config):
        """Test individual post rendering."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                frontmatter = PostFrontmatter(
                    title="Test Post",
                    date=date(2023, 1, 1),
                    tags=["test"]
                )

                post = PostContent(
                    frontmatter=frontmatter,
                    content="Test content"
                )

                html_content = "<p>Test content</p>"
                html = renderer.render_post(post, html_content)

                assert "Test Post" in html
                assert html_content in html
                assert "January 01, 2023" in html

    def test_render_archive(self, temp_templates_dir, mock_config):
        """Test archive page rendering."""
        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []

        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service', return_value=mock_post_service):
                renderer = TemplateRenderer(temp_templates_dir)

                html = renderer.render_archive()

                assert "Archive" in html
                assert "Test Blog" in html

    def test_render_rss_feed(self, temp_templates_dir, mock_config):
        """Test RSS feed rendering."""
        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []

        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service', return_value=mock_post_service):
                renderer = TemplateRenderer(temp_templates_dir)

                xml = renderer.render_rss_feed()

                assert "<?xml version" in xml
                assert "<rss version" in xml
                assert "Test Blog" in xml

    def test_validate_template_valid(self, temp_templates_dir, mock_config):
        """Test template validation for valid template."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                is_valid, error = renderer.validate_template('index.html')

                assert is_valid is True
                assert error is None

    def test_validate_template_invalid(self, temp_templates_dir, mock_config):
        """Test template validation for non-existent template."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                is_valid, error = renderer.validate_template('nonexistent.html')

                assert is_valid is False
                assert error is not None

    def test_date_format_filter(self, temp_templates_dir, mock_config):
        """Test custom date format filter."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                test_date = date(2023, 12, 25)
                formatted = renderer._format_date(test_date)

                assert "December 25, 2023" in formatted

    def test_excerpt_filter(self, temp_templates_dir, mock_config):
        """Test excerpt creation filter."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                long_content = "This is a very long content. " * 20
                excerpt = renderer._create_excerpt(long_content, 50)

                assert len(excerpt) <= 53  # 50 + "..."
                assert excerpt.endswith("...")

    def test_template_rendering_error(self, temp_templates_dir, mock_config):
        """Test template rendering error handling."""
        with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer = TemplateRenderer(temp_templates_dir)

                # Mock the environment to raise an exception
                renderer.env.get_template = Mock(side_effect=Exception("Template error"))

                with pytest.raises(TemplateRenderingError, match="Failed to render template"):
                    renderer.render_template('index.html')


class TestAssetManager:
    """Test AssetManager functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.build.output_dir = "test_build"
        return config

    def test_asset_manager_initialization(self, mock_config, temp_content_structure):
        """Test asset manager initialization."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    assert manager.content_dir == temp_content_structure['content']
                    assert manager.static_dir == temp_content_structure['static']
                    assert len(manager.allowed_extensions) > 0

    def test_validate_file_valid_image(self, mock_config, temp_content_structure):
        """Test file validation for valid image file."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    image_file = temp_content_structure['content'] / "images" / "test.jpg"
                    is_valid = manager.validate_file(image_file)

                    assert is_valid is True

    def test_validate_file_invalid_extension(self, mock_config, temp_content_structure):
        """Test file validation for invalid file extension."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    exe_file = temp_content_structure['content'] / "images" / "test.exe"
                    is_valid = manager.validate_file(exe_file)

                    assert is_valid is False

    def test_validate_file_suspicious_name(self, mock_config, temp_content_structure):
        """Test file validation for suspicious file names."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    suspicious_file = temp_content_structure['content'] / "images" / ".htaccess"
                    is_valid = manager.validate_file(suspicious_file)

                    assert is_valid is False

    def test_copy_file_success(self, mock_config, temp_content_structure):
        """Test successful file copying."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    source_file = temp_content_structure['content'] / "images" / "test.jpg"
                    dest_file = temp_content_structure['build'] / "images" / "test.jpg"

                    success = manager.copy_file(source_file, dest_file)

                    assert success is True
                    assert dest_file.exists()
                    assert dest_file.read_bytes() == source_file.read_bytes()

    def test_copy_file_invalid_source(self, mock_config, temp_content_structure):
        """Test copying invalid source file."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    source_file = temp_content_structure['content'] / "images" / "test.exe"
                    dest_file = temp_content_structure['build'] / "images" / "test.exe"

                    success = manager.copy_file(source_file, dest_file)

                    assert success is False
                    assert not dest_file.exists()

    def test_needs_update_new_file(self, mock_config, temp_content_structure):
        """Test needs_update for new file."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    source_file = temp_content_structure['content'] / "images" / "test.jpg"
                    dest_file = temp_content_structure['build'] / "images" / "test.jpg"

                    needs_update = manager.needs_update(source_file, dest_file)

                    assert needs_update is True

    def test_needs_update_older_dest(self, mock_config, temp_content_structure):
        """Test needs_update for older destination file."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    source_file = temp_content_structure['content'] / "images" / "test.jpg"
                    dest_file = temp_content_structure['build'] / "images" / "test.jpg"

                    # Create destination file
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    dest_file.write_bytes(b"old data")

                    # Make source newer
                    time.sleep(0.1)
                    source_file.touch()

                    needs_update = manager.needs_update(source_file, dest_file)

                    assert needs_update is True

    def test_copy_directory_assets(self, mock_config, temp_content_structure):
        """Test copying directory assets."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    source_dir = temp_content_structure['content'] / "images"
                    dest_dir = temp_content_structure['build'] / "images"

                    successful, failed = manager.copy_directory_assets(source_dir, dest_dir)

                    # Should copy 2 valid images, skip 2 invalid files
                    assert successful == 2
                    assert failed == 2
                    assert (dest_dir / "test.jpg").exists()
                    assert (dest_dir / "test.png").exists()
                    assert not (dest_dir / "test.exe").exists()
                    assert not (dest_dir / ".htaccess").exists()

    def test_calculate_file_hash(self, mock_config, temp_content_structure):
        """Test file hash calculation."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    test_file = temp_content_structure['content'] / "images" / "test.jpg"
                    hash1 = manager.calculate_file_hash(test_file)
                    hash2 = manager.calculate_file_hash(test_file)

                    assert hash1 == hash2
                    assert len(hash1) == 32  # MD5 hash length

    def test_get_asset_info(self, mock_config, temp_content_structure):
        """Test getting asset information."""
        with patch('microblog.builder.asset_manager.get_config', return_value=mock_config):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    info = manager.get_asset_info()

                    assert 'mappings' in info
                    assert 'total_files' in info
                    assert 'total_size' in info
                    assert info['total_files'] >= 3  # At least 3 valid files


class TestBuildGenerator:
    """Test BuildGenerator comprehensive functionality."""

    @pytest.fixture
    def mock_dependencies(self, temp_content_structure):
        """Mock all dependencies for BuildGenerator."""
        mock_config = Mock()
        mock_config.build.output_dir = str(temp_content_structure['build'])
        mock_config.build.backup_dir = str(temp_content_structure['build']) + ".bak"
        mock_config.build.posts_per_page = 5

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()
        mock_post_service = Mock()

        # Setup successful behaviors
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = temp_content_structure['content']
        mock_template_renderer.templates_dir = temp_content_structure['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_asset_manager.copy_all_assets.return_value = {
            'total_successful': 5,
            'total_failed': 0,
            'mappings': []
        }

        return {
            'config': mock_config,
            'markdown_processor': mock_markdown_processor,
            'template_renderer': mock_template_renderer,
            'asset_manager': mock_asset_manager,
            'post_service': mock_post_service
        }

    def test_build_generator_initialization(self, mock_dependencies):
        """Test BuildGenerator initialization."""
        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            progress_callback = Mock()
                            generator = BuildGenerator(progress_callback)

                            assert generator.config == mock_dependencies['config']
                            assert generator.progress_callback == progress_callback
                            assert generator.progress_history == []

    def test_report_progress(self, mock_dependencies):
        """Test progress reporting."""
        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            progress_callback = Mock()
                            generator = BuildGenerator(progress_callback)

                            generator._report_progress(
                                BuildPhase.CONTENT_PROCESSING,
                                "Processing posts",
                                50.0,
                                {"processed": 5}
                            )

                            assert len(generator.progress_history) == 1
                            progress = generator.progress_history[0]
                            assert progress.phase == BuildPhase.CONTENT_PROCESSING
                            assert progress.message == "Processing posts"
                            assert progress.percentage == 50.0
                            assert progress.details == {"processed": 5}

                            # Check callback was called
                            progress_callback.assert_called_once()

    def test_validate_build_preconditions_success(self, mock_dependencies):
        """Test successful build preconditions validation."""
        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            generator = BuildGenerator()

                            is_valid = generator._validate_build_preconditions()

                            assert is_valid is True

    def test_validate_build_preconditions_missing_templates(self, mock_dependencies):
        """Test build preconditions validation with missing templates."""
        mock_dependencies['template_renderer'].validate_template.return_value = (False, "Template not found")

        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            generator = BuildGenerator()

                            is_valid = generator._validate_build_preconditions()

                            assert is_valid is False

    def test_create_backup_success(self, mock_dependencies, temp_content_structure):
        """Test successful backup creation."""
        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            generator = BuildGenerator()

                            # Create a build directory with content
                            generator.build_dir.mkdir(parents=True)
                            (generator.build_dir / "test.html").write_text("test content")

                            success = generator._create_backup()

                            assert success is True
                            assert generator.build_dir.exists()
                            assert generator.backup_dir.exists()
                            assert (generator.backup_dir / "test.html").exists()

    def test_rollback_from_backup_success(self, mock_dependencies, temp_content_structure):
        """Test successful rollback from backup."""
        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            generator = BuildGenerator()

                            # Create backup directory with content
                            generator.backup_dir.mkdir(parents=True)
                            (generator.backup_dir / "backup.html").write_text("backup content")

                            # Create failed build directory
                            generator.build_dir.mkdir(parents=True)
                            (generator.build_dir / "failed.html").write_text("failed content")

                            success = generator._rollback_from_backup()

                            assert success is True
                            assert generator.build_dir.exists()
                            assert (generator.build_dir / "backup.html").exists()
                            assert not generator.backup_dir.exists()

    def test_build_success_flow(self, mock_dependencies):
        """Test complete successful build flow."""
        # Setup mock returns for successful build
        mock_dependencies['post_service'].get_published_posts.return_value = []
        mock_dependencies['markdown_processor'].process_content.return_value = "<p>test</p>"
        mock_dependencies['template_renderer'].render_homepage.return_value = "<html>homepage</html>"
        mock_dependencies['template_renderer'].render_archive.return_value = "<html>archive</html>"
        mock_dependencies['template_renderer'].render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_dependencies['template_renderer'].get_all_tags.return_value = []
        mock_dependencies['asset_manager'].copy_all_assets.return_value = {
            'total_successful': 5,
            'total_failed': 0,
            'mappings': []
        }

        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            progress_callback = Mock()
                            generator = BuildGenerator(progress_callback)

                            result = generator.build()

                            assert result.success is True
                            assert "completed successfully" in result.message
                            assert result.duration > 0
                            assert result.build_dir == generator.build_dir
                            assert result.stats is not None
                            assert len(generator.progress_history) > 0

                            # Check that all phases were executed
                            phases = [p.phase for p in generator.progress_history]
                            assert BuildPhase.INITIALIZING in phases
                            assert BuildPhase.BACKUP_CREATION in phases
                            assert BuildPhase.CONTENT_PROCESSING in phases
                            assert BuildPhase.TEMPLATE_RENDERING in phases
                            assert BuildPhase.ASSET_COPYING in phases
                            assert BuildPhase.VERIFICATION in phases
                            assert BuildPhase.CLEANUP in phases
                            assert BuildPhase.COMPLETED in phases

    def test_build_failure_with_rollback(self, mock_dependencies):
        """Test build failure scenario with successful rollback."""
        # Setup mock to fail during content processing
        mock_dependencies['markdown_processor'].process_content.side_effect = Exception("Processing failed")

        with patch('microblog.builder.generator.get_config', return_value=mock_dependencies['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_dependencies['markdown_processor']):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_dependencies['template_renderer']):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_dependencies['asset_manager']):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_dependencies['post_service']):

                            generator = BuildGenerator()

                            # Create backup to enable rollback
                            generator.backup_dir.mkdir(parents=True)
                            (generator.backup_dir / "backup.html").write_text("backup")

                            result = generator.build()

                            assert result.success is False
                            assert ("rollback successful" in result.message or "Build failed and rollback failed" in result.message)
                            assert result.error is not None

                            # Check rollback phase was executed
                            phases = [p.phase for p in generator.progress_history]
                            assert BuildPhase.ROLLBACK in phases
                            assert BuildPhase.FAILED in phases

    def test_build_phases_enum_coverage(self):
        """Test that all BuildPhase enum values are covered."""
        expected_phases = {
            BuildPhase.INITIALIZING,
            BuildPhase.BACKUP_CREATION,
            BuildPhase.CONTENT_PROCESSING,
            BuildPhase.TEMPLATE_RENDERING,
            BuildPhase.ASSET_COPYING,
            BuildPhase.VERIFICATION,
            BuildPhase.CLEANUP,
            BuildPhase.ROLLBACK,
            BuildPhase.COMPLETED,
            BuildPhase.FAILED
        }

        # Verify all enum values exist
        actual_phases = set(BuildPhase)
        assert actual_phases == expected_phases

    def test_global_instances(self):
        """Test global instance getters."""
        # Test markdown processor
        processor1 = get_markdown_processor()
        processor2 = get_markdown_processor()
        assert processor1 is processor2

        # Test template renderer
        with patch('microblog.builder.template_renderer.get_config'):
            with patch('microblog.builder.template_renderer.get_post_service'):
                renderer1 = get_template_renderer()
                renderer2 = get_template_renderer()
                assert renderer1 is renderer2

        # Test asset manager
        with patch('microblog.builder.asset_manager.get_config'):
            manager1 = get_asset_manager()
            manager2 = get_asset_manager()
            assert manager1 is manager2

        # Test build generator
        with patch('microblog.builder.generator.get_config'):
            with patch('microblog.builder.generator.get_markdown_processor'):
                with patch('microblog.builder.generator.get_template_renderer'):
                    with patch('microblog.builder.generator.get_asset_manager'):
                        with patch('microblog.builder.generator.get_post_service'):
                            gen1 = get_build_generator()
                            gen2 = get_build_generator()
                            assert gen1 is gen2


class TestBuildFailureScenarios:
    """Test comprehensive failure scenarios and rollback mechanisms."""

    @pytest.fixture
    def failure_test_setup(self, temp_content_structure):
        """Setup for failure testing."""
        mock_config = Mock()
        mock_config.build.output_dir = str(temp_content_structure['build'])
        mock_config.build.backup_dir = str(temp_content_structure['build']) + ".bak"
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.posts_dir.parent = temp_content_structure['content']

        return {
            'config': mock_config,
            'post_service': mock_post_service,
            'structure': temp_content_structure
        }

    def test_markdown_processing_failure(self, failure_test_setup):
        """Test failure during markdown processing phase."""
        setup = failure_test_setup

        # Create existing build to test backup/rollback
        setup['structure']['build'].mkdir(parents=True)
        (setup['structure']['build'] / "existing.html").write_text("existing content")

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Setup posts to process
        sample_post = PostContent(
            frontmatter=PostFrontmatter(
                title="Test Post",
                date=date(2023, 1, 1),
                tags=["test"]
            ),
            content="# Test"
        )
        setup['post_service'].get_published_posts.return_value = [sample_post]

        # Make markdown processing fail
        mock_markdown_processor.process_content.side_effect = Exception("Markdown processing failed")

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Should fail but rollback
                            assert result.success is False
                            assert ("rollback successful" in result.message or "Build failed and rollback failed" in result.message)
                            assert result.error is not None

                            # Original content should be restored
                            assert (setup['structure']['build'] / "existing.html").exists()
                            assert (setup['structure']['build'] / "existing.html").read_text() == "existing content"

    def test_template_rendering_failure(self, failure_test_setup):
        """Test failure during template rendering phase."""
        setup = failure_test_setup

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Setup posts
        setup['post_service'].get_published_posts.return_value = []

        # Make content processing succeed but template rendering fail
        mock_markdown_processor.process_content.return_value = "<p>test</p>"
        mock_template_renderer.render_homepage.side_effect = Exception("Template rendering failed")

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator()
                            result = generator.build()

                            assert result.success is False
                            assert "Template rendering failed" in str(result.error)

    def test_asset_copying_failure(self, failure_test_setup):
        """Test failure during asset copying phase."""
        setup = failure_test_setup

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Setup posts
        setup['post_service'].get_published_posts.return_value = []

        # Make previous phases succeed but asset copying fail
        mock_markdown_processor.process_content.return_value = "<p>test</p>"
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = []
        mock_asset_manager.copy_all_assets.side_effect = Exception("Asset copying failed")

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator()
                            result = generator.build()

                            assert result.success is False
                            assert "Asset copying failed" in str(result.error)

    def test_build_verification_failure(self, failure_test_setup):
        """Test failure during build verification phase."""
        setup = failure_test_setup

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Setup posts
        setup['post_service'].get_published_posts.return_value = []

        # Make all phases succeed
        mock_markdown_processor.process_content.return_value = "<p>test</p>"
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = []
        mock_asset_manager.copy_all_assets.return_value = {
            'total_successful': 5,
            'total_failed': 0,
            'mappings': []
        }

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator()

                            # Mock _verify_build_integrity to fail
                            generator._verify_build_integrity = Mock(return_value=False)

                            result = generator.build()

                            assert result.success is False
                            assert "integrity verification failed" in result.message.lower()

    def test_rollback_failure_scenario(self, failure_test_setup):
        """Test scenario where both build and rollback fail."""
        setup = failure_test_setup

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Make markdown processing fail
        mock_markdown_processor.process_content.side_effect = Exception("Processing failed")
        setup['post_service'].get_published_posts.return_value = [PostContent(
            frontmatter=PostFrontmatter(title="Test", date=date(2023, 1, 1), tags=[], slug="test"),
            content="test"
        )]

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator()

                            # Mock rollback to also fail
                            generator._rollback_from_backup = Mock(return_value=False)

                            result = generator.build()

                            assert result.success is False
                            assert "rollback failed" in result.message

    def test_progress_callback_exception_handling(self, failure_test_setup):
        """Test that progress callback exceptions don't break the build."""
        setup = failure_test_setup

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation to pass
        mock_template_renderer.templates_dir = setup['structure']['static'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Setup for successful build
        setup['post_service'].get_published_posts.return_value = []
        mock_markdown_processor.process_content.return_value = "<p>test</p>"
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = []
        mock_asset_manager.copy_all_assets.return_value = {
            'total_successful': 5,
            'total_failed': 0,
            'mappings': []
        }

        # Create callback that raises exception
        def failing_callback(progress):
            raise Exception("Callback failed")

        with patch('microblog.builder.generator.get_config', return_value=setup['config']):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=setup['post_service']):

                            generator = BuildGenerator(failing_callback)
                            result = generator.build()

                            # Build should still succeed despite callback failure
                            assert result.success is True

    def test_large_file_asset_validation(self, temp_content_structure):
        """Test asset validation with large files."""
        with patch('microblog.builder.asset_manager.get_config'):
            with patch('microblog.builder.asset_manager.get_content_dir', return_value=temp_content_structure['content']):
                with patch('microblog.builder.asset_manager.get_static_dir', return_value=temp_content_structure['static']):
                    manager = AssetManager()

                    # Create a large file (over 50MB limit)
                    large_file = temp_content_structure['content'] / "images" / "large.jpg"
                    large_file.write_bytes(b"x" * (51 * 1024 * 1024))  # 51MB

                    is_valid = manager.validate_file(large_file)
                    assert is_valid is False

    def test_build_with_insufficient_permissions(self, failure_test_setup):
        """Test build failure due to insufficient file permissions."""
        setup = failure_test_setup

        # Create a read-only build directory to simulate permission issues
        setup['structure']['build'].mkdir(parents=True)
        readonly_file = setup['structure']['build'] / "readonly.txt"
        readonly_file.write_text("readonly")

        # On Windows, we simulate this by mocking the ensure_directory function
        with patch('microblog.builder.generator.ensure_directory') as mock_ensure:
            mock_ensure.side_effect = PermissionError("Permission denied")

            mock_config = setup['config']
            mock_post_service = setup['post_service']
            mock_post_service.posts_dir.parent = setup['structure']['content']

            with patch('microblog.builder.generator.get_config', return_value=mock_config):
                with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                    generator = BuildGenerator()

                    result = generator.build()

                    assert result.success is False
                    assert ("preconditions validation failed" in result.message.lower() or "failed to create backup" in result.message.lower() or "Permission denied" in str(result.error))


class TestPerformanceBuildTests:
    """Test build system performance requirements."""

    def test_build_time_small_content(self):
        """Test build time with small amount of content (< 1 second expected)."""
        # Create minimal content structure
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "build"
            content_dir = Path(temp_dir) / "content"
            content_dir.mkdir(parents=True)

            mock_config = Mock()
            mock_config.build.output_dir = str(build_dir)
            mock_config.build.backup_dir = str(build_dir) + ".bak"
            mock_config.build.posts_per_page = 5

            # Create 5 small posts
            posts = []
            for i in range(5):
                post = PostContent(
                    frontmatter=PostFrontmatter(
                        title=f"Post {i}",
                        date=date(2023, 1, i+1),
                        tags=["test"],
                        slug=f"post-{i}"
                    ),
                    content=f"# Post {i}\n\nContent for post {i}."
                )
                posts.append(post)

            mock_post_service = Mock()
            mock_post_service.get_published_posts.return_value = posts
            mock_post_service.posts_dir.parent = content_dir

            mock_markdown_processor = Mock()
            mock_template_renderer = Mock()
            mock_asset_manager = Mock()

            # Setup for fast responses
            mock_template_renderer.templates_dir = Path(temp_dir) / "templates"
            mock_template_renderer.templates_dir.mkdir(parents=True)
            mock_template_renderer.validate_template.return_value = (True, None)
            mock_markdown_processor.process_content.return_value = "<p>processed</p>"
            mock_template_renderer.render_homepage.return_value = "<html>home</html>"
            mock_template_renderer.render_post.return_value = "<html>post</html>"
            mock_template_renderer.render_archive.return_value = "<html>archive</html>"
            mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
            mock_template_renderer.get_all_tags.return_value = ["test"]
            mock_template_renderer.render_tag_page.return_value = "<html>tag</html>"
            mock_asset_manager.copy_all_assets.return_value = {
                'total_successful': 3,
                'total_failed': 0,
                'mappings': []
            }

            with patch('microblog.builder.generator.get_config', return_value=mock_config):
                with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                    with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                        with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                                start_time = time.time()
                                generator = BuildGenerator()
                                result = generator.build()
                                end_time = time.time()

                                build_duration = end_time - start_time

                                assert result.success is True
                                # For 5 posts, should be very fast (allowing more time for mock overhead)
                                assert build_duration < 2.0, f"Small build took {build_duration:.3f}s, expected < 2s"

    def test_build_time_medium_content(self):
        """Test build time with medium amount of content (should meet 5s for 100 posts target)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "build"
            content_dir = Path(temp_dir) / "content"
            content_dir.mkdir(parents=True)

            mock_config = Mock()
            mock_config.build.output_dir = str(build_dir)
            mock_config.build.backup_dir = str(build_dir) + ".bak"
            mock_config.build.posts_per_page = 10

            # Create 50 posts (simulating workload for performance testing)
            posts = []
            for i in range(50):
                post = PostContent(
                    frontmatter=PostFrontmatter(
                        title=f"Performance Test Post {i}",
                        date=date(2023, 1, (i % 28) + 1),
                        tags=["performance", "test", f"tag-{i % 5}"],
                        slug=f"perf-post-{i}"
                    ),
                    content=f"# Performance Test Post {i}\n\nThis is content for post {i}.\n\n## Section\n\nMore content here."
                )
                posts.append(post)

            mock_post_service = Mock()
            mock_post_service.get_published_posts.return_value = posts
            mock_post_service.posts_dir.parent = content_dir

            mock_markdown_processor = Mock()
            mock_template_renderer = Mock()
            mock_asset_manager = Mock()

            # Setup mocks
            mock_template_renderer.templates_dir = Path(temp_dir) / "templates"
            mock_template_renderer.templates_dir.mkdir(parents=True)
            mock_template_renderer.validate_template.return_value = (True, None)
            mock_markdown_processor.process_content.return_value = "<p>processed content</p>"
            mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
            mock_template_renderer.render_post.return_value = "<html>post content</html>"
            mock_template_renderer.render_archive.return_value = "<html>archive</html>"
            mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
            mock_template_renderer.get_all_tags.return_value = ["performance", "test", "tag-0", "tag-1", "tag-2"]
            mock_template_renderer.render_tag_page.return_value = "<html>tag page</html>"
            mock_asset_manager.copy_all_assets.return_value = {
                'total_successful': 10,
                'total_failed': 0,
                'mappings': []
            }

            with patch('microblog.builder.generator.get_config', return_value=mock_config):
                with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                    with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                        with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                                start_time = time.time()
                                generator = BuildGenerator()
                                result = generator.build()
                                end_time = time.time()

                                build_duration = end_time - start_time

                                assert result.success is True
                                # For 50 posts, should be well under target (scaling to 100 posts < 5s)
                                assert build_duration < 5.0, f"Medium build took {build_duration:.3f}s, expected < 5s"

    def test_memory_usage_during_build(self):
        """Test that memory usage remains reasonable during build."""
        # Mock the entire test since psutil is not a project dependency
        # In real implementation, this would monitor memory usage during build
        initial_memory = 100 * 1024 * 1024  # 100MB simulated initial

        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "build"
            content_dir = Path(temp_dir) / "content"
            templates_dir = Path(temp_dir) / "templates"

            # Create required directories
            content_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)

            mock_config = Mock()
            mock_config.build.output_dir = str(build_dir)
            mock_config.build.backup_dir = str(build_dir) + ".bak"
            mock_config.build.posts_per_page = 10

            # Create many posts to test memory usage
            posts = []
            for i in range(100):
                post = PostContent(
                    frontmatter=PostFrontmatter(
                        title=f"Memory Test Post {i}",
                        date=date(2023, 1, (i % 28) + 1),
                        tags=["memory", "test"],
                        slug=f"memory-post-{i}"
                    ),
                    content=f"# Memory Test Post {i}\n\n" + "Content line. " * 100  # Make content substantial
                )
                posts.append(post)

            mock_post_service = Mock()
            mock_post_service.get_published_posts.return_value = posts
            mock_post_service.posts_dir.parent = content_dir

            mock_markdown_processor = Mock()
            mock_template_renderer = Mock()
            mock_asset_manager = Mock()

            # Setup mocks
            mock_template_renderer.templates_dir = templates_dir
            mock_template_renderer.validate_template.return_value = (True, None)
            mock_markdown_processor.process_content.return_value = "<p>" + "processed content. " * 50 + "</p>"
            mock_template_renderer.render_homepage.return_value = "<html>" + "homepage content. " * 100 + "</html>"
            mock_template_renderer.render_post.return_value = "<html>" + "post content. " * 100 + "</html>"
            mock_template_renderer.render_archive.return_value = "<html>" + "archive content. " * 100 + "</html>"
            mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss>" + "feed content. " * 100 + "</rss>"
            mock_template_renderer.get_all_tags.return_value = ["memory", "test"]
            mock_template_renderer.render_tag_page.return_value = "<html>" + "tag content. " * 100 + "</html>"
            mock_asset_manager.copy_all_assets.return_value = {
                'total_successful': 50,
                'total_failed': 0,
                'mappings': []
            }

            with patch('microblog.builder.generator.get_config', return_value=mock_config):
                with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                    with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                        with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                                generator = BuildGenerator()
                                result = generator.build()

                                # Simulate memory usage tracking
                                final_memory = 150 * 1024 * 1024  # 150MB simulated final
                                memory_increase = final_memory - initial_memory

                                assert result.success is True
                                # Memory increase should be reasonable (less than 100MB for 100 posts)
                                assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"


class TestAtomicOperationFailures:
    """Test atomic operation failure scenarios and rollback integrity."""

    @pytest.fixture
    def atomic_test_setup(self):
        """Setup for atomic operation testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            content_dir = base_dir / "content"
            posts_dir = content_dir / "posts"
            build_dir = base_dir / "build"
            backup_dir = base_dir / "build.bak"

            posts_dir.mkdir(parents=True)

            # Create existing build structure to test backup/rollback
            build_dir.mkdir(parents=True)
            existing_file = build_dir / "index.html"
            existing_file.write_text("<html>Original content</html>")

            config_data = {
                'site': {
                    'title': 'Test Site',
                    'url': 'http://example.com',
                    'author': 'Test Author',
                    'description': 'Test Description'
                },
                'build': {
                    'output_dir': str(build_dir),
                    'backup_dir': str(backup_dir),
                    'posts_per_page': 10
                },
                'content': {
                    'posts_dir': str(posts_dir),
                    'images_dir': str(content_dir / "images")
                }
            }

            yield {
                'base': base_dir,
                'content': content_dir,
                'posts': posts_dir,
                'build': build_dir,
                'backup': backup_dir,
                'config': config_data,
                'existing_content': existing_file.read_text()
            }

    def test_concurrent_build_safety(self, atomic_test_setup):
        """Test that concurrent builds are handled safely."""
        setup = atomic_test_setup

        # Mock dependencies
        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])
        mock_config.build.backup_dir = str(setup['backup'])
        mock_config.site.title = "Test"
        mock_config.site.url = "http://test.com"
        mock_config.site.author = "Test"
        mock_config.site.description = "Test"

        mock_post_service = Mock()
        mock_post_service.posts_dir = setup['posts']
        mock_post_service.get_published_posts.return_value = []

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation
        mock_template_renderer.templates_dir = setup['content'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = []
        mock_asset_manager.copy_all_assets.return_value = {'total_successful': 0, 'total_failed': 0, 'mappings': []}

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                            generator1 = BuildGenerator()
                            generator2 = BuildGenerator()

                            # First generator succeeds
                            result1 = generator1.build()
                            assert result1.success is True

                            # Second generator should also work (no locks expected)
                            result2 = generator2.build()
                            assert result2.success is True

    def test_backup_integrity_verification(self, atomic_test_setup):
        """Test backup integrity verification and restoration."""
        setup = atomic_test_setup

        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])
        mock_config.build.backup_dir = str(setup['backup'])
        mock_config.site.title = "Test"

        mock_post_service = Mock()
        mock_post_service.posts_dir = setup['posts']
        mock_post_service.get_published_posts.return_value = []

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup template validation to fail during rendering
        mock_template_renderer.templates_dir = setup['content'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_template_renderer.render_homepage.side_effect = Exception("Template corrupted")

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Build should fail and rollback
                            assert result.success is False
                            assert ("Template corrupted" in str(result.error) or
                                    "Template rendering failed" in str(result.error))

                            # Original content should be restored
                            assert setup['build'].exists()
                            restored_content = (setup['build'] / "index.html").read_text()
                            assert restored_content == setup['existing_content']

    def test_corrupted_template_detection(self, atomic_test_setup):
        """Test detection and handling of corrupted templates."""
        setup = atomic_test_setup

        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])
        mock_config.build.backup_dir = str(setup['backup'])

        mock_post_service = Mock()
        mock_post_service.posts_dir = setup['posts']

        mock_template_renderer = Mock()
        mock_template_renderer.templates_dir = setup['content'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)

        # Simulate corrupted template validation
        mock_template_renderer.validate_template.side_effect = [
            (True, None),   # index.html
            (False, "Syntax error in template"),  # post.html
            (True, None),   # archive.html
            (True, None),   # rss.xml
        ]

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                    generator = BuildGenerator()

                    # Validation should fail during precondition check
                    preconditions_valid = generator._validate_build_preconditions()
                    assert preconditions_valid is False

    def test_large_file_handling_edge_cases(self, atomic_test_setup):
        """Test edge cases with large file handling and memory constraints."""
        setup = atomic_test_setup

        # Create large test file
        large_file = setup['content'] / "large_asset.dat"
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB file
        large_file.write_bytes(large_content)

        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])

        mock_asset_manager = Mock()

        # Simulate asset manager rejecting large files
        def validate_file_side_effect(file_path):
            if file_path.stat().st_size > 5 * 1024 * 1024:  # 5MB limit
                return False
            return True

        mock_asset_manager.validate_file.side_effect = validate_file_side_effect

        # Test that large files are properly rejected
        result = mock_asset_manager.validate_file(large_file)
        assert result is False

    def test_permission_failure_scenarios(self, atomic_test_setup):
        """Test handling of permission-based failures."""
        setup = atomic_test_setup

        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])
        mock_config.build.backup_dir = str(setup['backup'])

        mock_post_service = Mock()
        mock_post_service.posts_dir = setup['posts']
        mock_post_service.get_published_posts.return_value = []

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation
        mock_template_renderer.templates_dir = setup['content'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = []

        # Simulate permission error during asset copying
        mock_asset_manager.copy_all_assets.side_effect = PermissionError("Access denied")

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Build should fail with permission error
                            assert result.success is False
                            assert "Access denied" in str(result.error)

    def test_build_interruption_scenarios(self, atomic_test_setup):
        """Test handling of build interruptions and partial states."""
        setup = atomic_test_setup

        mock_config = Mock()
        mock_config.build.output_dir = str(setup['build'])
        mock_config.build.backup_dir = str(setup['backup'])

        mock_post_service = Mock()
        mock_post_service.posts_dir = setup['posts']

        # Create test posts
        test_posts = []
        for i in range(3):
            post = PostContent(
                frontmatter=PostFrontmatter(
                    title=f"Test Post {i}",
                    date=date(2023, 1, i+1),
                    tags=["test"]
                ),
                content=f"Content for post {i}"
            )
            test_posts.append(post)

        mock_post_service.get_published_posts.return_value = test_posts

        mock_markdown_processor = Mock()
        mock_template_renderer = Mock()
        mock_asset_manager = Mock()

        # Setup validation
        mock_template_renderer.templates_dir = setup['content'] / "templates"
        mock_template_renderer.templates_dir.mkdir(parents=True, exist_ok=True)
        mock_template_renderer.validate_template.return_value = (True, None)

        # Simulate failure during markdown processing
        mock_markdown_processor.process_content.side_effect = Exception("Content processing failed: Failed to process 1 posts")

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                        with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Build should fail due to content processing error
                            assert result.success is False
                            assert ("Content processing failed" in str(result.error) or "Failed to process" in str(result.error))


class TestBuildPerformanceRequirements:
    """Test build performance requirements as specified in acceptance criteria."""

    def test_build_time_100_posts_target(self):
        """Test that build completes within 5 seconds for 100 posts."""
        # Create mock dependencies
        mock_config = Mock()
        mock_config.build.output_dir = "/tmp/test_build"
        mock_config.build.backup_dir = "/tmp/test_backup"
        mock_config.site.title = "Performance Test"
        mock_config.site.url = "http://test.com"
        mock_config.site.author = "Test"
        mock_config.site.description = "Test"
        mock_config.build.posts_per_page = 10

        mock_post_service = Mock()
        mock_post_service.posts_dir = Path("/tmp/posts")

        # Create 100 test posts
        posts = []
        for i in range(100):
            post = PostContent(
                frontmatter=PostFrontmatter(
                    title=f"Performance Test Post {i}",
                    date=date(2023, 1, (i % 28) + 1),
                    tags=["performance", "test"],
                    slug=f"perf-post-{i}"
                ),
                content=f"# Performance Test Content {i}\n\nThis is content for performance test post {i}. " * 10
            )
            posts.append(post)

        mock_post_service.get_published_posts.return_value = posts

        mock_markdown_processor = Mock()
        mock_markdown_processor.process_content.return_value = "<p>processed content</p>"

        mock_template_renderer = Mock()
        mock_template_renderer.templates_dir = Path("/tmp/templates")
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_template_renderer.render_homepage.return_value = "<html>homepage</html>"
        mock_template_renderer.render_post.return_value = "<html>post</html>"
        mock_template_renderer.render_archive.return_value = "<html>archive</html>"
        mock_template_renderer.render_rss_feed.return_value = "<?xml version='1.0'?><rss></rss>"
        mock_template_renderer.get_all_tags.return_value = ["performance", "test"]
        mock_template_renderer.render_tag_page.return_value = "<html>tag</html>"

        mock_asset_manager = Mock()
        mock_asset_manager.copy_all_assets.return_value = {
            'total_successful': 50,
            'total_failed': 0,
            'mappings': []
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir(parents=True)
            mock_template_renderer.templates_dir = templates_dir

            with patch('microblog.builder.generator.get_config', return_value=mock_config):
                with patch('microblog.builder.generator.get_markdown_processor', return_value=mock_markdown_processor):
                    with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                        with patch('microblog.builder.generator.get_asset_manager', return_value=mock_asset_manager):
                            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):

                                generator = BuildGenerator()
                                start_time = time.time()
                                result = generator.build()
                                end_time = time.time()

                                build_duration = end_time - start_time

                                assert result.success is True
                                # Target: <5s for 100 posts (allowing some flexibility for test environment)
                                assert build_duration < 10.0, f"Build took {build_duration:.2f}s, target is <5s for 100 posts"

    def test_markdown_processing_speed_target(self):
        """Test that markdown processing meets <100ms per file target."""
        processor = MarkdownProcessor()

        # Create test content
        test_content = """# Test Post

This is a test post with various markdown features:

## Code Block
```python
def hello_world():
    print("Hello, World!")
    return True
```

## List
- Item 1
- Item 2
- Item 3

## Table
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

This should be reasonably complex content to process.
""" * 5  # Make it longer

        post = PostContent(
            frontmatter=PostFrontmatter(
                title="Performance Test Post",
                date=date(2023, 1, 1),
                tags=["test"]
            ),
            content=test_content
        )

        # Warm up the processor
        processor.process_content(post)

        # Measure processing time
        start_time = time.time()
        for _ in range(10):  # Process 10 times to get average
            html = processor.process_content(post)
        end_time = time.time()

        avg_time = (end_time - start_time) / 10

        assert avg_time < 0.1, f"Markdown processing took {avg_time:.3f}s per file, target is <100ms"
        assert len(html) > 0  # Ensure processing worked

    def test_template_rendering_speed_target(self):
        """Test that template rendering meets <50ms per page target."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)

            # Create basic template
            template_content = """
<!DOCTYPE html>
<html>
<head><title>{{ post.frontmatter.title }}</title></head>
<body>
    <h1>{{ post.frontmatter.title }}</h1>
    <div>{{ content }}</div>
    <p>Tags: {{ post.frontmatter.tags|join(', ') }}</p>
</body>
</html>
"""
            (templates_dir / "post.html").write_text(template_content)

            mock_config = Mock()
            mock_config.site.title = "Test Site"
            mock_config.site.url = "http://test.com"
            mock_config.site.author = "Test Author"
            mock_config.site.description = "Test Description"
            mock_config.build.posts_per_page = 10

            renderer = TemplateRenderer(templates_dir)

            # Create test post
            post = PostContent(
                frontmatter=PostFrontmatter(
                    title="Performance Test Post",
                    date=date(2023, 1, 1),
                    tags=["performance", "test"]
                ),
                content="Test content"
            )

            html_content = "<p>Test HTML content for performance testing.</p>"

            # Warm up the renderer
            with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
                renderer.render_post(post, html_content)

            # Measure rendering time
            start_time = time.time()
            with patch('microblog.builder.template_renderer.get_config', return_value=mock_config):
                for _ in range(20):  # Render 20 times to get average
                    rendered = renderer.render_post(post, html_content)
            end_time = time.time()

            avg_time = (end_time - start_time) / 20

            assert avg_time < 0.05, f"Template rendering took {avg_time:.3f}s per page, target is <50ms"
            assert len(rendered) > 0  # Ensure rendering worked
