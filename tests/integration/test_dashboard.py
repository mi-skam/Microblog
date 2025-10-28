"""
Fixed integration tests for dashboard functionality and user workflows.

This module tests the complete dashboard interface using a simplified approach
that properly mocks the authentication and template systems to ensure stable test execution.
"""

import os
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates


class TestDashboardIntegrationFixed:
    """Fixed integration tests for dashboard functionality."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with all required structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create content structure
            content_dir = base_dir / "content"
            data_dir = content_dir / "_data"
            posts_dir = content_dir / "posts"
            templates_dir = content_dir / "templates"
            static_dir = content_dir / "static"

            data_dir.mkdir(parents=True)
            posts_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)
            static_dir.mkdir(parents=True)

            # Create sample templates
            self._create_dashboard_templates(templates_dir)

            # Create config file
            config_data = self._create_test_config(str(base_dir))
            config_file = base_dir / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            yield {
                'base': base_dir,
                'content': content_dir,
                'data': data_dir,
                'posts': posts_dir,
                'templates': templates_dir,
                'static': static_dir,
                'config': config_file
            }

    def _create_dashboard_templates(self, templates_dir: Path):
        """Create minimal dashboard templates for testing."""
        # Dashboard home template
        dashboard_home = """<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body>
    <h1>Dashboard</h1>
    <div class="stats">
        <span>Total: {{ stats.total_posts }}</span>
        <span>Published: {{ stats.published_posts }}</span>
        <span>Drafts: {{ stats.draft_posts }}</span>
    </div>
    <div class="recent-posts">
        {% for post in recent_posts %}
        <div class="post-item">{{ post.frontmatter.title }}</div>
        {% endfor %}
    </div>
</body>
</html>"""
        (templates_dir / "dashboard").mkdir(exist_ok=True)
        (templates_dir / "dashboard" / "home.html").write_text(dashboard_home)

        # Posts list template
        posts_list = """<!DOCTYPE html>
<html>
<head><title>Posts</title></head>
<body>
    <h1>Posts</h1>
    <div class="stats">{{ stats.total_posts }} total posts</div>
    <div class="posts-list">
        {% for post in all_posts %}
        <div class="post-item" data-slug="{{ post.computed_slug }}">
            <h3>{{ post.frontmatter.title }}</h3>
            <p>{{ post.frontmatter.date }}</p>
            {% if post.is_draft %}<span class="draft">Draft</span>{% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
        (templates_dir / "dashboard" / "posts_list.html").write_text(posts_list)

        # Post edit template
        post_edit = """<!DOCTYPE html>
<html>
<head><title>{{ "Edit" if is_edit else "New" }} Post</title></head>
<body>
    <h1>{{ "Edit" if is_edit else "New" }} Post</h1>
    <form method="post" action="{{ '/dashboard/api/posts/' + post.computed_slug if is_edit else '/dashboard/api/posts' }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="title" value="{{ post.frontmatter.title if is_edit else '' }}" required>
        <textarea name="content">{{ post.content if is_edit else '' }}</textarea>
        <input type="text" name="tags" value="{{ post.frontmatter.tags | join(', ') if is_edit else '' }}">
        <input type="checkbox" name="draft" {% if is_edit and post.is_draft %}checked{% endif %}>
        <button type="submit">Save</button>
    </form>
</body>
</html>"""
        (templates_dir / "dashboard" / "post_edit.html").write_text(post_edit)

        # Settings template
        settings = """<!DOCTYPE html>
<html>
<head><title>Settings</title></head>
<body>
    <h1>Settings</h1>
    <div class="settings-form">
        <h2>Site Configuration</h2>
        <p>Settings management interface</p>
    </div>
</body>
</html>"""
        (templates_dir / "dashboard" / "settings.html").write_text(settings)

        # Pages list template
        pages_list = """<!DOCTYPE html>
<html>
<head><title>Pages</title></head>
<body>
    <h1>Pages</h1>
    <div class="pages-list">
        {% for page in pages %}
        <div class="page-item">{{ page.title }}</div>
        {% endfor %}
    </div>
</body>
</html>"""
        (templates_dir / "dashboard" / "pages_list.html").write_text(pages_list)

        # Auth login template
        (templates_dir / "auth").mkdir(exist_ok=True)
        login_template = """<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h1>Login</h1>
    <form method="post" action="/auth/login">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="username" required>
        <input type="password" name="password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>"""
        (templates_dir / "auth" / "login.html").write_text(login_template)

    def _create_test_config(self, base_dir: str) -> dict:
        """Create test configuration data."""
        return {
            'site': {
                'title': 'Test Dashboard Blog',
                'url': 'https://test-dashboard.example.com',
                'author': 'Test Author',
                'description': 'Dashboard integration test blog'
            },
            'build': {
                'output_dir': f"{base_dir}/build",
                'backup_dir': f"{base_dir}/build.bak",
                'posts_per_page': 5
            },
            'auth': {
                'jwt_secret': 'test-dashboard-secret-key-that-is-long-enough-for-testing-purposes',
                'session_expires': 3600
            }
        }

    @pytest.fixture
    def minimal_app(self, temp_project_dir):
        """Create a minimal FastAPI app for testing dashboard routes."""
        app = FastAPI()

        # Set up templates
        app.state.templates = Jinja2Templates(directory=str(temp_project_dir['templates']))

        # Import and include the dashboard router
        from microblog.server.routes.dashboard import router as dashboard_router
        app.include_router(dashboard_router)

        return app

    @pytest.fixture
    def authenticated_client(self, minimal_app, temp_project_dir):
        """Create authenticated test client with direct route testing."""
        mock_user = {
            'user_id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'role': 'admin'
        }

        with patch('microblog.server.middleware.get_current_user', return_value=mock_user), \
             patch('microblog.server.routes.dashboard.get_current_user', return_value=mock_user), \
             patch('microblog.server.middleware.get_csrf_token', return_value='test-csrf-token'), \
             patch('microblog.server.routes.dashboard.get_csrf_token', return_value='test-csrf-token'), \
             patch('microblog.utils.get_content_dir', return_value=temp_project_dir['content']):

            yield TestClient(minimal_app)

    def test_dashboard_home_route_functionality(self, authenticated_client):
        """Test dashboard home route functionality with mocked services."""
        # Mock post service to return sample posts
        mock_posts = [
            Mock(
                frontmatter=Mock(title="Test Post 1", date=date(2023, 12, 1), tags=["test"]),
                is_draft=False,
                computed_slug="test-post-1"
            ),
            Mock(
                frontmatter=Mock(title="Test Post 2", date=date(2023, 12, 2), tags=["test"]),
                is_draft=True,
                computed_slug="test-post-2"
            )
        ]

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.list_posts.return_value = mock_posts
            mock_service.return_value.get_published_posts.return_value = [mock_posts[0]]
            mock_service.return_value.get_draft_posts.return_value = [mock_posts[1]]

            response = authenticated_client.get("/dashboard/")

            assert response.status_code == 200
            assert "Dashboard" in response.text
            assert "Total: 2" in response.text
            assert "Published: 1" in response.text
            assert "Drafts: 1" in response.text
            assert "Test Post 1" in response.text

    def test_posts_list_route_functionality(self, authenticated_client):
        """Test posts listing route functionality."""
        mock_posts = [
            Mock(
                frontmatter=Mock(title="Published Post", date=date(2023, 12, 1), tags=["test"]),
                is_draft=False,
                computed_slug="published-post"
            ),
            Mock(
                frontmatter=Mock(title="Draft Post", date=date(2023, 12, 2), tags=["test"]),
                is_draft=True,
                computed_slug="draft-post"
            )
        ]

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.list_posts.return_value = mock_posts

            response = authenticated_client.get("/dashboard/posts")

            assert response.status_code == 200
            assert "Posts" in response.text
            assert "2 total posts" in response.text
            assert "Published Post" in response.text
            assert "Draft Post" in response.text
            assert 'data-slug="published-post"' in response.text
            assert 'class="draft"' in response.text

    def test_new_post_form_route(self, authenticated_client):
        """Test new post form route functionality."""
        response = authenticated_client.get("/dashboard/posts/new")

        assert response.status_code == 200
        assert "New Post" in response.text
        assert 'name="title"' in response.text
        assert 'name="content"' in response.text
        assert 'name="csrf_token"' in response.text
        assert 'action="/dashboard/api/posts"' in response.text

    def test_edit_post_form_route(self, authenticated_client):
        """Test edit post form route functionality."""
        mock_post = Mock(
            frontmatter=Mock(
                title="Test Post to Edit",
                date=date(2023, 12, 1),
                tags=["test", "edit"]
            ),
            content="# Test Content",
            is_draft=False,
            computed_slug="test-post-edit"
        )

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.get_post_by_slug.return_value = mock_post

            response = authenticated_client.get("/dashboard/posts/test-post-edit/edit")

            assert response.status_code == 200
            assert "Edit Post" in response.text
            assert "Test Post to Edit" in response.text
            assert "# Test Content" in response.text
            assert "test, edit" in response.text
            assert 'action="/dashboard/api/posts/test-post-edit"' in response.text

    def test_settings_route(self, authenticated_client):
        """Test settings page route functionality."""
        response = authenticated_client.get("/dashboard/settings")

        assert response.status_code == 200
        assert "Settings" in response.text
        assert "Site Configuration" in response.text

    def test_pages_list_route(self, authenticated_client):
        """Test pages listing route functionality."""
        response = authenticated_client.get("/dashboard/pages")

        assert response.status_code == 200
        assert "Pages" in response.text

    def test_create_post_api_route(self, authenticated_client):
        """Test post creation API route functionality."""
        mock_post = Mock(
            frontmatter=Mock(title="New API Post"),
            computed_slug="new-api-post"
        )

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.create_post.return_value = mock_post

            post_data = {
                "title": "New API Post",
                "content": "# API Post Content",
                "tags": "api, test",
                "draft": "false",
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts", data=post_data, follow_redirects=False)

            assert response.status_code == 303
            assert response.headers["location"] == "/dashboard/posts"

            # Verify post service was called correctly
            mock_service.return_value.create_post.assert_called_once()
            call_args = mock_service.return_value.create_post.call_args
            assert call_args.kwargs["title"] == "New API Post"
            assert call_args.kwargs["content"] == "# API Post Content"
            assert call_args.kwargs["tags"] == ["api", "test"]
            assert call_args.kwargs["draft"] is False

    def test_create_post_validation_error(self, authenticated_client):
        """Test post creation with validation errors."""
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            from microblog.content.post_service import PostValidationError
            mock_service.return_value.create_post.side_effect = PostValidationError("Title is required")

            post_data = {
                "title": "",  # Empty title should cause validation error
                "content": "Content",
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts", data=post_data)
            assert response.status_code == 400
            assert "Title is required" in response.text

    def test_update_post_api_route(self, authenticated_client):
        """Test post update API route functionality."""
        mock_post = Mock(
            frontmatter=Mock(title="Updated Post"),
            computed_slug="updated-post"
        )

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.update_post.return_value = mock_post

            post_data = {
                "title": "Updated Post Title",
                "content": "# Updated Content",
                "tags": "updated, test",
                "draft": "true",
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts/test-slug", data=post_data, follow_redirects=False)

            assert response.status_code == 303
            assert response.headers["location"] == "/dashboard/posts"

            # Verify update was called correctly
            mock_service.return_value.update_post.assert_called_once()
            call_args = mock_service.return_value.update_post.call_args
            assert call_args.kwargs["slug"] == "test-slug"
            assert call_args.kwargs["title"] == "Updated Post Title"
            assert call_args.kwargs["draft"] is True

    def test_update_nonexistent_post_api(self, authenticated_client):
        """Test updating non-existent post via API."""
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            from microblog.content.post_service import PostNotFoundError
            mock_service.return_value.update_post.side_effect = PostNotFoundError("Post not found")

            post_data = {
                "title": "Updated Title",
                "content": "Updated content",
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts/nonexistent", data=post_data)
            assert response.status_code == 404

    def test_complete_workflow_simulation(self, authenticated_client):
        """Test complete workflow simulation from creation to editing."""
        # Step 1: Access new post form
        new_post_response = authenticated_client.get("/dashboard/posts/new")
        assert new_post_response.status_code == 200
        assert "New Post" in new_post_response.text

        # Step 2: Create new post
        mock_created_post = Mock(
            frontmatter=Mock(title="Workflow Test Post"),
            computed_slug="workflow-test-post"
        )

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.create_post.return_value = mock_created_post

            create_data = {
                "title": "Workflow Test Post",
                "content": "# Initial Content",
                "tags": "workflow, test",
                "draft": "true",
                "csrf_token": "test-csrf-token"
            }

            create_response = authenticated_client.post("/dashboard/api/posts", data=create_data, follow_redirects=False)
            assert create_response.status_code == 303
            assert create_response.headers["location"] == "/dashboard/posts"

            # Step 3: Access edit form for created post
            mock_edit_post = Mock(
                frontmatter=Mock(
                    title="Workflow Test Post",
                    date=date(2023, 12, 1),
                    tags=["workflow", "test"]
                ),
                content="# Initial Content",
                is_draft=True,
                computed_slug="workflow-test-post"
            )

            mock_service.return_value.get_post_by_slug.return_value = mock_edit_post

            edit_form_response = authenticated_client.get("/dashboard/posts/workflow-test-post/edit")
            assert edit_form_response.status_code == 200
            assert "Edit Post" in edit_form_response.text
            assert "Workflow Test Post" in edit_form_response.text

            # Step 4: Update the post
            mock_updated_post = Mock(
                frontmatter=Mock(title="Updated Workflow Post"),
                computed_slug="workflow-test-post"
            )

            mock_service.return_value.update_post.return_value = mock_updated_post

            update_data = {
                "title": "Updated Workflow Post",
                "content": "# Updated Content",
                "tags": "workflow, test, updated",
                "draft": "false",  # Publish the post
                "csrf_token": "test-csrf-token"
            }

            update_response = authenticated_client.post("/dashboard/api/posts/workflow-test-post", data=update_data, follow_redirects=False)
            assert update_response.status_code == 303
            assert update_response.headers["location"] == "/dashboard/posts"

            # Verify all service calls were made correctly
            assert mock_service.return_value.create_post.called
            assert mock_service.return_value.get_post_by_slug.called
            assert mock_service.return_value.update_post.called

    def test_error_handling_scenarios(self, authenticated_client):
        """Test various error handling scenarios."""
        # Test dashboard error handling when post service fails
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.list_posts.side_effect = Exception("Database error")

            response = authenticated_client.get("/dashboard/")
            assert response.status_code == 500

        # Test posts list error handling when post service fails
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.list_posts.side_effect = Exception("Service error")

            response = authenticated_client.get("/dashboard/posts")
            assert response.status_code == 500

        # Test editing non-existent post
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.get_post_by_slug.side_effect = Exception("Post not found")

            response = authenticated_client.get("/dashboard/posts/nonexistent/edit")
            assert response.status_code == 404

    def test_draft_vs_published_posts_handling(self, authenticated_client):
        """Test proper handling of draft vs published posts."""
        # Create mock posts with different draft states
        mock_posts = [
            Mock(
                frontmatter=Mock(title="Published Post 1", date=date(2023, 12, 1), tags=["published"]),
                is_draft=False,
                computed_slug="published-post-1"
            ),
            Mock(
                frontmatter=Mock(title="Draft Post 1", date=date(2023, 12, 2), tags=["draft"]),
                is_draft=True,
                computed_slug="draft-post-1"
            ),
            Mock(
                frontmatter=Mock(title="Published Post 2", date=date(2023, 12, 3), tags=["published"]),
                is_draft=False,
                computed_slug="published-post-2"
            )
        ]

        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            mock_service.return_value.list_posts.return_value = mock_posts
            published_posts = [p for p in mock_posts if not p.is_draft]
            draft_posts = [p for p in mock_posts if p.is_draft]
            mock_service.return_value.get_published_posts.return_value = published_posts
            mock_service.return_value.get_draft_posts.return_value = draft_posts

            response = authenticated_client.get("/dashboard/")
            assert response.status_code == 200

            # Verify statistics are correct
            assert "Total: 3" in response.text
            assert "Published: 2" in response.text
            assert "Drafts: 1" in response.text

            # Test posts list view
            posts_response = authenticated_client.get("/dashboard/posts")
            assert posts_response.status_code == 200
            assert "3 total posts" in posts_response.text
            assert "Published Post 1" in posts_response.text
            assert "Draft Post 1" in posts_response.text
            assert 'class="draft"' in posts_response.text

    def test_post_service_integration_scenarios(self, authenticated_client):
        """Test integration with post service for various scenarios."""
        # Test service errors during post creation
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            from microblog.content.post_service import PostFileError
            mock_service.return_value.create_post.side_effect = PostFileError("Failed to write file")

            post_data = {
                "title": "Test Post",
                "content": "Test content",
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts", data=post_data)
            assert response.status_code == 500
            assert "Failed to write file" in response.text

        # Test various validation scenarios
        with patch('microblog.server.routes.dashboard.get_post_service') as mock_service:
            from microblog.content.post_service import PostValidationError
            mock_service.return_value.create_post.side_effect = PostValidationError("Content cannot be empty")

            post_data = {
                "title": "Valid Title",
                "content": "",  # Empty content
                "csrf_token": "test-csrf-token"
            }

            response = authenticated_client.post("/dashboard/api/posts", data=post_data)
            assert response.status_code == 400
            assert "Content cannot be empty" in response.text