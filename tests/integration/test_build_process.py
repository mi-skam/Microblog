"""
Integration tests for the complete build process.

This module tests the entire build pipeline including markdown processing,
template rendering, asset management, and atomic build operations with
realistic content and failure scenarios.
"""

import tempfile
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from microblog.builder.generator import BuildGenerator, BuildPhase, build_site
from microblog.content.validators import PostContent, PostFrontmatter


class TestIntegrationBuildProcess:
    """Integration tests for complete build process."""

    @pytest.fixture
    def real_project_structure(self):
        """Create realistic project structure for integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create content structure
            content_dir = base_dir / "content"
            posts_dir = content_dir / "posts"
            posts_dir.mkdir(parents=True)

            # Create data directory for SQLite
            data_dir = content_dir / "_data"
            data_dir.mkdir(parents=True)

            # Create images directory
            images_dir = content_dir / "images"
            images_dir.mkdir(parents=True)

            # Create static directories
            static_dir = base_dir / "static"
            templates_dir = static_dir / "templates"
            css_dir = static_dir / "css"
            js_dir = static_dir / "js"
            templates_dir.mkdir(parents=True)
            css_dir.mkdir(parents=True)
            js_dir.mkdir(parents=True)

            # Create build and backup directories
            build_dir = base_dir / "build"
            backup_dir = base_dir / "build.bak"

            # Create sample posts
            self._create_sample_posts(posts_dir)

            # Create sample images
            self._create_sample_images(images_dir)

            # Create templates
            self._create_sample_templates(templates_dir)

            # Create static assets
            self._create_sample_static_assets(css_dir, js_dir)

            # Create configuration
            config_data = self._create_sample_config(str(build_dir), str(backup_dir))

            yield {
                'base': base_dir,
                'content': content_dir,
                'posts': posts_dir,
                'data': data_dir,
                'images': images_dir,
                'static': static_dir,
                'templates': templates_dir,
                'css': css_dir,
                'js': js_dir,
                'build': build_dir,
                'backup': backup_dir,
                'config': config_data
            }

    def _create_sample_posts(self, posts_dir: Path):
        """Create sample markdown posts."""
        # Post 1: Regular post
        post1_content = """---
title: "My First Blog Post"
date: 2023-12-01
tags:
  - "python"
  - "web development"
draft: false
---

# Welcome to My Blog

This is my first blog post about **Python** and web development.

## Code Example

Here's a simple Python function:

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```

## List Example

- Item 1
- Item 2
- Item 3

Check out my [website](https://example.com) for more content.
"""
        (posts_dir / "first-post.md").write_text(post1_content, encoding='utf-8')

        # Post 2: Post with complex formatting
        post2_content = """---
title: "Advanced Python Features"
date: 2023-12-05
tags:
  - "python"
  - "advanced"
draft: false
---

# Advanced Python Features

This post covers some advanced Python features.

## Table Example

| Feature | Description | Usefulness |
|---------|-------------|------------|
| Decorators | Function wrappers | High |
| Generators | Memory efficient | Very High |
| Context Managers | Resource management | High |

## Code Block with Language

```javascript
// JavaScript example
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}
```

## Task List

- [x] Learn Python basics
- [x] Understand decorators
- [ ] Master async/await
- [ ] Build web applications

> This is a blockquote with important information.
"""
        (posts_dir / "advanced-python.md").write_text(post2_content, encoding='utf-8')

        # Post 3: Draft post (should not be built)
        post3_content = """---
title: "Draft Post"
date: 2023-12-10
tags:
  - "draft"
draft: true
---

# This is a Draft

This post should not appear in the build.
"""
        (posts_dir / "draft-post.md").write_text(post3_content, encoding='utf-8')

        # Post 4: Future dated post
        future_date = datetime.now().date().replace(year=datetime.now().year + 1)
        post4_content = f"""---
title: "Future Post"
date: {future_date.isoformat()}
tags:
  - "future"
draft: false
---

# Future Post

This post is dated in the future.
"""
        (posts_dir / "future-post.md").write_text(post4_content, encoding='utf-8')

    def _create_sample_images(self, images_dir: Path):
        """Create sample image files."""
        # Create fake image files
        (images_dir / "hero.jpg").write_bytes(b"fake JPEG data for hero image")
        (images_dir / "logo.png").write_bytes(b"fake PNG data for logo")
        (images_dir / "thumbnail.webp").write_bytes(b"fake WebP data")

        # Create subdirectory with images
        gallery_dir = images_dir / "gallery"
        gallery_dir.mkdir()
        (gallery_dir / "photo1.jpg").write_bytes(b"fake photo 1")
        (gallery_dir / "photo2.jpg").write_bytes(b"fake photo 2")

    def _create_sample_templates(self, templates_dir: Path):
        """Create sample Jinja2 templates."""
        # Base template
        base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ site.title }}{% endblock %}</title>
    <link rel="stylesheet" href="/css/style.css">
    <link rel="alternate" type="application/rss+xml" title="{{ site.title }}" href="/rss.xml">
</head>
<body>
    <header>
        <h1><a href="/">{{ site.title }}</a></h1>
        <p>{{ site.description }}</p>
        <nav>
            <a href="/">Home</a>
            <a href="/archive.html">Archive</a>
        </nav>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; {{ current_year }} {{ site.author }}</p>
    </footer>
    <script src="/js/main.js"></script>
</body>
</html>"""
        (templates_dir / "base.html").write_text(base_template)

        # Homepage template
        index_template = """{% extends "base.html" %}

{% block content %}
<section class="recent-posts">
    <h2>Recent Posts</h2>
    {% if posts %}
        {% for post in posts %}
        <article class="post-preview">
            <h3><a href="/posts/{{ post.computed_slug }}.html">{{ post.frontmatter.title }}</a></h3>
            <p class="meta">{{ post.frontmatter.date | dateformat }} • Tags:
                {% for tag in post.frontmatter.tags %}
                    <a href="/tags/{{ tag.lower() }}.html">{{ tag }}</a>{% if not loop.last %}, {% endif %}
                {% endfor %}
            </p>
            <div class="excerpt">
                {{ post.content | process_markdown | excerpt(200) | safe }}
            </div>
        </article>
        {% endfor %}
    {% else %}
        <p>No posts yet. Check back later!</p>
    {% endif %}
</section>
{% endblock %}"""
        (templates_dir / "index.html").write_text(index_template)

        # Post template
        post_template = """{% extends "base.html" %}

{% block title %}{{ post.frontmatter.title }} - {{ site.title }}{% endblock %}

{% block content %}
<article class="post">
    <header class="post-header">
        <h1>{{ post.frontmatter.title }}</h1>
        <p class="meta">
            Published on {{ post.frontmatter.date | dateformat }} by {{ site.author }}
        </p>
        <div class="tags">
            {% for tag in post.frontmatter.tags %}
                <a href="/tags/{{ tag.lower() }}.html" class="tag">{{ tag }}</a>
            {% endfor %}
        </div>
    </header>
    <div class="post-content">
        {{ content | safe }}
    </div>
</article>
{% endblock %}"""
        (templates_dir / "post.html").write_text(post_template)

        # Archive template
        archive_template = """{% extends "base.html" %}

{% block title %}Archive - {{ site.title }}{% endblock %}

{% block content %}
<section class="archive">
    <h1>Archive</h1>
    {% if posts_by_year %}
        {% for year, year_posts in posts_by_year.items() %}
        <section class="year-group">
            <h2>{{ year }}</h2>
            <ul class="post-list">
                {% for post in year_posts %}
                <li>
                    <a href="/posts/{{ post.computed_slug }}.html">{{ post.frontmatter.title }}</a>
                    <span class="date">{{ post.frontmatter.date | dateformat('%b %d') }}</span>
                </li>
                {% endfor %}
            </ul>
        </section>
        {% endfor %}
    {% else %}
        <p>No posts in the archive yet.</p>
    {% endif %}
</section>
{% endblock %}"""
        (templates_dir / "archive.html").write_text(archive_template)

        # RSS template
        rss_template = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{{ site.title }}</title>
    <link>{{ site.url }}</link>
    <description>{{ site.description }}</description>
    <language>en-us</language>
    <lastBuildDate>{{ build_date | rfc2822 }}</lastBuildDate>
    <atom:link href="{{ site.url }}/rss.xml" rel="self" type="application/rss+xml" />

    {% for post in posts %}
    <item>
        <title>{{ post.frontmatter.title }}</title>
        <link>{{ site.url }}/posts/{{ post.computed_slug }}.html</link>
        <pubDate>{{ post.pub_date | rfc2822 }}</pubDate>
        <guid>{{ site.url }}/posts/{{ post.computed_slug }}.html</guid>
        <description><![CDATA[{{ post.content | process_markdown | excerpt(300) | safe }}]]></description>
    </item>
    {% endfor %}
</channel>
</rss>"""
        (templates_dir / "rss.xml").write_text(rss_template)

        # Tag template
        tag_template = """{% extends "base.html" %}

{% block title %}Posts tagged "{{ tag }}" - {{ site.title }}{% endblock %}

{% block content %}
<section class="tag-page">
    <h1>Posts tagged "{{ tag }}"</h1>
    {% if posts %}
        <ul class="post-list">
            {% for post in posts %}
            <li>
                <a href="/posts/{{ post.computed_slug }}.html">{{ post.frontmatter.title }}</a>
                <span class="date">{{ post.frontmatter.date | dateformat }}</span>
            </li>
            {% endfor %}
        </ul>
    {% else %}
        <p>No posts found with this tag.</p>
    {% endif %}
</section>
{% endblock %}"""
        (templates_dir / "tag.html").write_text(tag_template)

    def _create_sample_static_assets(self, css_dir: Path, js_dir: Path):
        """Create sample static assets."""
        # CSS file
        css_content = """/* Main stylesheet */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    border-bottom: 1px solid #eee;
    margin-bottom: 40px;
    padding-bottom: 20px;
}

header h1 a {
    text-decoration: none;
    color: #333;
}

nav a {
    margin-right: 20px;
    text-decoration: none;
    color: #666;
}

.post-preview {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
}

.meta {
    color: #666;
    font-size: 0.9em;
}

.tag {
    background: #f0f0f0;
    padding: 2px 8px;
    border-radius: 3px;
    text-decoration: none;
    color: #333;
    font-size: 0.8em;
}

.highlight {
    background: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px;
    overflow-x: auto;
}

table {
    border-collapse: collapse;
    width: 100%;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #f5f5f5;
}

blockquote {
    border-left: 4px solid #ddd;
    margin: 0;
    padding-left: 20px;
    font-style: italic;
}
"""
        (css_dir / "style.css").write_text(css_content)

        # JavaScript file
        js_content = """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Blog loaded successfully');

    // Add smooth scrolling for anchor links
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add copy button to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.className = 'copy-button';
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent);
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
        block.parentNode.insertBefore(button, block);
    });
});
"""
        (js_dir / "main.js").write_text(js_content)

    def _create_sample_config(self, build_dir: str, backup_dir: str) -> dict[str, Any]:
        """Create sample configuration."""
        return {
            'site': {
                'title': 'Integration Test Blog',
                'url': 'https://integration-test.example.com',
                'author': 'Test Author',
                'description': 'A test blog for integration testing'
            },
            'build': {
                'output_dir': build_dir,
                'backup_dir': backup_dir,
                'posts_per_page': 5
            },
            'server': {
                'host': '127.0.0.1',
                'port': 8080,
                'hot_reload': True
            },
            'auth': {
                'jwt_secret': 'integration-test-secret-key-that-is-long-enough-for-testing',
                'session_expires': 3600
            }
        }

    def test_complete_build_process_success(self, real_project_structure):
        """Test complete successful build process with real content."""
        structure = real_project_structure

        # Mock configuration and services
        mock_config = Mock()
        mock_config.site.title = structure['config']['site']['title']
        mock_config.site.url = structure['config']['site']['url']
        mock_config.site.author = structure['config']['site']['author']
        mock_config.site.description = structure['config']['site']['description']
        mock_config.build.output_dir = structure['config']['build']['output_dir']
        mock_config.build.backup_dir = structure['config']['build']['backup_dir']
        mock_config.build.posts_per_page = structure['config']['build']['posts_per_page']

        # Create sample published posts
        published_posts = []
        for post_file in structure['posts'].glob("*.md"):
            if post_file.stem != "draft-post":  # Skip draft
                # Create PostContent objects for published posts
                frontmatter = PostFrontmatter(
                    title=f"Test Post {post_file.stem}",
                    date=date(2023, 12, 1),
                    tags=["test", "integration"],
                    slug=post_file.stem
                )
                post = PostContent(
                    frontmatter=frontmatter,
                    content=f"# Test Content for {post_file.stem}"
                )
                published_posts.append(post)

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = published_posts
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            # Execute build
                            progress_callback = Mock()
                            generator = BuildGenerator(progress_callback)
                            result = generator.build()

                            # Verify successful build
                            assert result.success is True
                            assert "completed successfully" in result.message
                            assert result.duration > 0
                            assert result.build_dir == structure['build']

                            # Verify build artifacts
                            assert structure['build'].exists()
                            assert (structure['build'] / "index.html").exists()
                            assert (structure['build'] / "archive.html").exists()
                            assert (structure['build'] / "rss.xml").exists()

                            # Verify posts directory and files
                            posts_dir = structure['build'] / "posts"
                            assert posts_dir.exists()

                            # Should have HTML files for published posts
                            html_files = list(posts_dir.glob("*.html"))
                            assert len(html_files) >= 2  # At least 2 non-draft posts

                            # Verify assets were copied
                            assert (structure['build'] / "css" / "style.css").exists()
                            assert (structure['build'] / "js" / "main.js").exists()
                            assert (structure['build'] / "images" / "hero.jpg").exists()

                            # Verify progress tracking
                            assert len(generator.progress_history) > 0
                            final_progress = generator.progress_history[-1]
                            assert final_progress.phase == BuildPhase.COMPLETED

    def test_build_with_empty_content(self, real_project_structure):
        """Test build process with no published posts."""
        structure = real_project_structure

        # Remove all posts
        for post_file in structure['posts'].glob("*.md"):
            post_file.unlink()

        mock_config = Mock()
        mock_config.site.title = "Empty Blog"
        mock_config.site.url = "https://empty.example.com"
        mock_config.site.author = "Empty Author"
        mock_config.site.description = "Empty blog"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Should still succeed with empty content
                            assert result.success is True
                            assert structure['build'].exists()
                            assert (structure['build'] / "index.html").exists()
                            assert (structure['build'] / "archive.html").exists()

                            # Posts directory might not exist or be empty
                            posts_dir = structure['build'] / "posts"
                            if posts_dir.exists():
                                html_files = list(posts_dir.glob("*.html"))
                                assert len(html_files) == 0

    def test_build_with_missing_templates(self, real_project_structure):
        """Test build process with missing required templates."""
        structure = real_project_structure

        # Remove required template
        (structure['templates'] / "index.html").unlink()

        mock_config = Mock()
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])

        mock_post_service = Mock()
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):

                    generator = BuildGenerator()
                    result = generator.build()

                    # Should fail due to missing template
                    assert result.success is False
                    assert "preconditions validation failed" in result.message.lower()

    def test_build_with_backup_and_rollback(self, real_project_structure):
        """Test build process with existing build, backup creation, and rollback."""
        structure = real_project_structure

        # Create existing build with content
        structure['build'].mkdir(parents=True)
        (structure['build'] / "old_index.html").write_text("Old content")
        (structure['build'] / "old_style.css").write_text("Old styles")

        mock_config = Mock()
        mock_config.site.title = "Test Blog"
        mock_config.site.url = "https://test.example.com"
        mock_config.site.author = "Test Author"
        mock_config.site.description = "Test Description"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        # Mock template renderer to fail after backup is created
        mock_template_renderer = Mock()
        mock_template_renderer.templates_dir = structure['templates']
        mock_template_renderer.validate_template.return_value = (True, None)
        mock_template_renderer.render_homepage.side_effect = Exception("Template rendering failed")

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.builder.generator.get_template_renderer', return_value=mock_template_renderer):
                    with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                        with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                            with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                                generator = BuildGenerator()
                                result = generator.build()

                                # Should fail but rollback successfully
                                assert result.success is False
                                assert "rollback successful" in result.message

                                # Original files should be restored
                                assert (structure['build'] / "old_index.html").exists()
                                assert (structure['build'] / "old_style.css").exists()

                                # Backup directory should not exist after rollback
                                assert not structure['backup'].exists()

    def test_build_performance_timing(self, real_project_structure):
        """Test build performance meets timing requirements."""
        structure = real_project_structure

        # Create more posts for performance testing
        for i in range(10):
            post_content = f"""---
title: "Performance Test Post {i}"
date: 2023-12-{1 + i:02d}
tags:
  - "performance"
  - "test"
draft: false
---

# Performance Test Post {i}

This is a performance test post with content.

## Code Block

```python
def test_function_{i}():
    return "test result {i}"
```

## Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row {i} A | Row {i} B | Row {i} C |

Some more content here to make the post substantial.
"""
            (structure['posts'] / f"perf-test-{i}.md").write_text(post_content)

        # Create multiple published posts
        published_posts = []
        for i in range(15):  # 15 posts total
            frontmatter = PostFrontmatter(
                title=f"Performance Test Post {i}",
                date=date(2023, 12, 1 + i),
                tags=["performance", "test"],
                slug=f"perf-test-{i}"
            )
            post = PostContent(
                frontmatter=frontmatter,
                content=f"# Performance Test Content {i}\n\nContent for post {i}"
            )
            published_posts.append(post)

        mock_config = Mock()
        mock_config.site.title = "Performance Test Blog"
        mock_config.site.url = "https://perf-test.example.com"
        mock_config.site.author = "Perf Test Author"
        mock_config.site.description = "Performance testing blog"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = published_posts
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            start_time = time.time()
                            generator = BuildGenerator()
                            result = generator.build()
                            end_time = time.time()

                            build_duration = end_time - start_time

                            # Verify successful build
                            assert result.success is True

                            # Performance requirement: should be much faster for small content
                            # For 15 posts, should be well under 5 seconds
                            assert build_duration < 5.0, f"Build took {build_duration:.2f}s, expected < 5s"

                            # Verify all posts were built
                            posts_dir = structure['build'] / "posts"
                            html_files = list(posts_dir.glob("*.html"))
                            assert len(html_files) == 15

    def test_build_site_convenience_function(self, real_project_structure):
        """Test the build_site convenience function."""
        structure = real_project_structure

        mock_config = Mock()
        mock_config.site.title = "Convenience Test"
        mock_config.site.url = "https://convenience.example.com"
        mock_config.site.author = "Test Author"
        mock_config.site.description = "Test Description"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            progress_callback = Mock()
                            result = build_site(progress_callback)

                            assert result.success is True
                            assert progress_callback.called

    def test_build_with_malformed_templates(self, real_project_structure):
        """Test build process with malformed Jinja2 templates."""
        structure = real_project_structure

        # Create malformed template
        malformed_template = """{% extends "base.html" %}

{% block content %}
<h1>{{ site.title }}</h1>
{% for post in posts %}
    <h2>{{ post.title }}</h2>
    <!-- Missing endfor tag -->
{% block %}"""
        (structure['templates'] / "index.html").write_text(malformed_template)

        mock_config = Mock()
        mock_config.site.title = "Malformed Test"
        mock_config.site.url = "https://malformed.example.com"
        mock_config.site.author = "Test Author"
        mock_config.site.description = "Test Description"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):

                    generator = BuildGenerator()
                    result = generator.build()

                    # Should fail due to malformed template
                    assert result.success is False

    def test_build_integrity_verification(self, real_project_structure):
        """Test build integrity verification process."""
        structure = real_project_structure

        mock_config = Mock()
        mock_config.site.title = "Integrity Test"
        mock_config.site.url = "https://integrity.example.com"
        mock_config.site.author = "Test Author"
        mock_config.site.description = "Test Description"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            generator = BuildGenerator()
                            result = generator.build()

                            # Should succeed and pass integrity verification
                            assert result.success is True

                            # Verify required files exist
                            assert (structure['build'] / "index.html").exists()
                            assert (structure['build'] / "archive.html").exists()
                            assert (structure['build'] / "rss.xml").exists()

                            # Check file sizes are reasonable (not empty)
                            assert (structure['build'] / "index.html").stat().st_size > 10
                            assert (structure['build'] / "archive.html").stat().st_size > 10
                            assert (structure['build'] / "rss.xml").stat().st_size > 10

    def test_concurrent_build_safety(self, real_project_structure):
        """Test that concurrent builds don't interfere with each other."""
        structure = real_project_structure

        mock_config = Mock()
        mock_config.site.title = "Concurrent Test"
        mock_config.site.url = "https://concurrent.example.com"
        mock_config.site.author = "Test Author"
        mock_config.site.description = "Test Description"
        mock_config.build.output_dir = str(structure['build'])
        mock_config.build.backup_dir = str(structure['backup'])
        mock_config.build.posts_per_page = 5

        mock_post_service = Mock()
        mock_post_service.get_published_posts.return_value = []
        mock_post_service.posts_dir.parent = structure['content']

        with patch('microblog.builder.generator.get_config', return_value=mock_config):
            with patch('microblog.builder.generator.get_post_service', return_value=mock_post_service):
                with patch('microblog.utils.get_templates_dir', return_value=structure['templates']):
                    with patch('microblog.utils.get_content_dir', return_value=structure['content']):
                        with patch('microblog.utils.get_static_dir', return_value=structure['static']):

                            # Create two separate generators
                            generator1 = BuildGenerator()
                            generator2 = BuildGenerator()

                            # Build with first generator
                            result1 = generator1.build()
                            assert result1.success is True

                            # Build with second generator should work
                            result2 = generator2.build()
                            assert result2.success is True

                            # Both should have independent progress histories
                            assert len(generator1.progress_history) > 0
                            assert len(generator2.progress_history) > 0
                            assert generator1.progress_history != generator2.progress_history
