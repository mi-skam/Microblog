"""
Dashboard routes for main interface showing post listings, statistics, and build status.

This module provides FastAPI routes for the dashboard interface including
the main dashboard view, post listing, and statistics display with HTMX support.
"""

import logging
from datetime import datetime, date

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from microblog.content.post_service import get_post_service, PostNotFoundError, PostValidationError, PostFileError
from microblog.server.middleware import get_csrf_token, get_current_user
from microblog.utils import get_content_dir

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize templates
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
templates = Jinja2Templates(directory=str(project_root / "templates"))


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


# API endpoints for post management
@router.post("/api/posts")
async def create_post_api(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    slug: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    date: str = Form(""),
    draft: str = Form("false")
):
    """
    Create a new post via API.

    Returns:
        Redirect to posts list on success, error response on failure
    """
    try:
        # Get current user (middleware ensures this exists for protected routes)
        user = get_current_user(request)

        # Get post service
        post_service = get_post_service()

        # Parse form data
        post_date = datetime.now().date() if not date else datetime.fromisoformat(date).date()
        post_tags = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        is_draft = draft.lower() in ("true", "1", "yes", "on")
        post_slug = slug.strip() if slug.strip() else None
        post_description = description.strip() if description.strip() else None

        # Create the post
        created_post = post_service.create_post(
            title=title,
            content=content,
            date=post_date,
            slug=post_slug,
            tags=post_tags,
            draft=is_draft,
            description=post_description
        )

        logger.info(f"Post created by user {user['username']}: {created_post.frontmatter.title}")

        # Redirect to posts list
        return RedirectResponse(url="/dashboard/posts", status_code=303)

    except PostValidationError as e:
        logger.error(f"Post validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PostFileError as e:
        logger.error(f"Post file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating post: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/posts/{slug}")
async def update_post_api(
    request: Request,
    slug: str,
    title: str = Form(...),
    content: str = Form(...),
    new_slug: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    date: str = Form(""),
    draft: str = Form("false")
):
    """
    Update an existing post via API.

    Args:
        slug: Current slug of the post to update

    Returns:
        Redirect to posts list on success, error response on failure
    """
    try:
        # Get current user (middleware ensures this exists for protected routes)
        user = get_current_user(request)

        # Get post service
        post_service = get_post_service()

        # Parse form data
        post_date = datetime.fromisoformat(date).date() if date else None
        post_tags = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        is_draft = draft.lower() in ("true", "1", "yes", "on")
        updated_slug = new_slug.strip() if new_slug.strip() else None
        post_description = description.strip() if description.strip() else None

        # Update the post
        updated_post = post_service.update_post(
            slug=slug,
            title=title,
            content=content,
            date=post_date,
            new_slug=updated_slug,
            tags=post_tags,
            draft=is_draft,
            description=post_description
        )

        logger.info(f"Post updated by user {user['username']}: {updated_post.frontmatter.title}")

        # Redirect to posts list
        return RedirectResponse(url="/dashboard/posts", status_code=303)

    except PostNotFoundError as e:
        logger.error(f"Post not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except PostValidationError as e:
        logger.error(f"Post validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PostFileError as e:
        logger.error(f"Post file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating post: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
