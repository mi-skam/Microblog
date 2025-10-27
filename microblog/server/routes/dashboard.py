"""
Dashboard routes for main interface showing post listings, statistics, and build status.

This module provides FastAPI routes for the dashboard interface including
the main dashboard view, post listing, and statistics display with HTMX support.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from microblog.content.post_service import get_post_service
from microblog.server.middleware import get_csrf_token, get_current_user
from microblog.utils import get_content_dir

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize templates
templates = Jinja2Templates(directory=str(get_content_dir() / "templates"))


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """
    Main dashboard page showing overview with post statistics and recent posts.

    Returns:
        HTML response with dashboard overview including statistics and recent posts
    """
    # Get current user (middleware ensures this exists for protected routes)
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    # Get post service
    post_service = get_post_service()

    try:
        # Get all posts for statistics
        all_posts = post_service.list_posts(include_drafts=True)
        published_posts = post_service.get_published_posts()
        draft_posts = post_service.get_draft_posts()

        # Get recent posts (last 5)
        recent_posts = post_service.list_posts(include_drafts=True, limit=5)

        # Calculate statistics
        stats = {
            "total_posts": len(all_posts),
            "published_posts": len(published_posts),
            "draft_posts": len(draft_posts),
            "recent_posts": len(recent_posts)
        }

        logger.info(f"Dashboard accessed by user {user['username']}")

        return templates.TemplateResponse(
            "dashboard/home.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "stats": stats,
                "recent_posts": recent_posts,
                "title": "Dashboard - Microblog",
                "current_year": datetime.now().year
            }
        )

    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return templates.TemplateResponse(
            "dashboard/home.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "error": "Failed to load dashboard data",
                "stats": {"total_posts": 0, "published_posts": 0, "draft_posts": 0, "recent_posts": 0},
                "recent_posts": [],
                "title": "Dashboard - Microblog",
                "current_year": datetime.now().year
            }
        )


@router.get("/posts", response_class=HTMLResponse)
async def posts_list(request: Request):
    """
    Posts listing page showing all posts with management controls.

    Returns:
        HTML response with comprehensive post listing interface
    """
    # Get current user and CSRF token
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    # Get post service
    post_service = get_post_service()

    try:
        # Get all posts (including drafts for admin view)
        all_posts = post_service.list_posts(include_drafts=True)

        # Separate published and draft posts for display
        published_posts = [post for post in all_posts if not post.is_draft]
        draft_posts = [post for post in all_posts if post.is_draft]

        # Calculate statistics
        stats = {
            "total_posts": len(all_posts),
            "published_posts": len(published_posts),
            "draft_posts": len(draft_posts)
        }

        logger.info(f"Posts list accessed by user {user['username']}, showing {len(all_posts)} posts")

        return templates.TemplateResponse(
            "dashboard/posts_list.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "all_posts": all_posts,
                "published_posts": published_posts,
                "draft_posts": draft_posts,
                "stats": stats,
                "title": "Posts - Dashboard",
                "current_year": datetime.now().year
            }
        )

    except Exception as e:
        logger.error(f"Error loading posts list: {e}")
        return templates.TemplateResponse(
            "dashboard/posts_list.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "error": "Failed to load posts",
                "all_posts": [],
                "published_posts": [],
                "draft_posts": [],
                "stats": {"total_posts": 0, "published_posts": 0, "draft_posts": 0},
                "title": "Posts - Dashboard",
                "current_year": datetime.now().year
            }
        )


@router.get("/posts/new", response_class=HTMLResponse)
async def new_post(request: Request):
    """
    New post creation form.

    Returns:
        HTML response with post creation form
    """
    # Get current user and CSRF token
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        "dashboard/post_edit.html",
        {
            "request": request,
            "user": user,
            "csrf_token": csrf_token,
            "title": "New Post - Dashboard",
            "is_edit": False,
            "current_year": datetime.now().year
        }
    )


@router.get("/posts/{slug}/edit", response_class=HTMLResponse)
async def edit_post(request: Request, slug: str):
    """
    Edit existing post form.

    Args:
        slug: Post slug to edit

    Returns:
        HTML response with post editing form pre-populated with existing data
    """
    # Get current user and CSRF token
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    # Get post service
    post_service = get_post_service()

    try:
        # Get the post to edit
        post = post_service.get_post_by_slug(slug, include_drafts=True)

        logger.info(f"Edit post form accessed for '{slug}' by user {user['username']}")

        return templates.TemplateResponse(
            "dashboard/post_edit.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "post": post,
                "title": f"Edit: {post.frontmatter.title} - Dashboard",
                "is_edit": True,
                "current_year": datetime.now().year
            }
        )

    except Exception as e:
        logger.error(f"Error loading post for editing: {e}")
        return templates.TemplateResponse(
            "dashboard/posts_list.html",
            {
                "request": request,
                "user": user,
                "csrf_token": csrf_token,
                "error": f"Post '{slug}' not found",
                "all_posts": [],
                "published_posts": [],
                "draft_posts": [],
                "stats": {"total_posts": 0, "published_posts": 0, "draft_posts": 0},
                "title": "Posts - Dashboard",
                "current_year": datetime.now().year
            }
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """
    Settings and configuration page.

    Returns:
        HTML response with settings interface
    """
    # Get current user and CSRF token
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        "dashboard/settings.html",
        {
            "request": request,
            "user": user,
            "csrf_token": csrf_token,
            "title": "Settings - Dashboard",
            "current_year": datetime.now().year
        }
    )


@router.get("/pages", response_class=HTMLResponse)
async def pages_list(request: Request):
    """
    Static pages listing and management.

    Returns:
        HTML response with pages listing interface
    """
    # Get current user and CSRF token
    user = get_current_user(request)
    csrf_token = get_csrf_token(request)

    # For now, just show a placeholder page
    # This will be implemented in future iterations
    return templates.TemplateResponse(
        "dashboard/pages_list.html",
        {
            "request": request,
            "user": user,
            "csrf_token": csrf_token,
            "title": "Pages - Dashboard",
            "pages": [],
            "current_year": datetime.now().year
        }
    )
