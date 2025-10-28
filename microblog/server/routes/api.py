"""
HTMX API endpoints for dynamic post operations.

This module provides API endpoints optimized for HTMX interactions, returning
HTML fragments instead of JSON responses for seamless frontend integration.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from microblog.builder.markdown_processor import (
    MarkdownProcessingError,
    get_markdown_processor,
)
from microblog.content.post_service import (
    PostFileError,
    PostNotFoundError,
    PostValidationError,
    get_post_service,
)
from microblog.server.middleware import require_authentication

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api", tags=["api"])


def _create_error_fragment(message: str, error_type: str = "error") -> str:
    """
    Create an HTML error fragment for HTMX responses.

    Args:
        message: Error message to display
        error_type: Type of error (error, warning, info)

    Returns:
        HTML fragment string
    """
    return f'''
    <div class="alert alert-{error_type}" hx-swap-oob="true" id="error-container">
        <p>{message}</p>
    </div>
    '''


def _create_success_fragment(message: str) -> str:
    """
    Create an HTML success fragment for HTMX responses.

    Args:
        message: Success message to display

    Returns:
        HTML fragment string
    """
    return f'''
    <div class="alert alert-success" hx-swap-oob="true" id="success-container">
        <p>{message}</p>
    </div>
    '''




@router.post("/posts", response_class=HTMLResponse)
async def create_post_htmx(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    slug: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    post_date: str = Form(""),
    draft: str = Form("false")
):
    """
    Create a new post via HTMX API.

    Returns:
        HTML fragment with success message or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get post service
        post_service = get_post_service()

        # Parse form data (same logic as dashboard.py)
        parsed_date = datetime.now().date() if not post_date else datetime.fromisoformat(post_date).date()
        post_tags = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        is_draft = draft.lower() in ("true", "1", "yes", "on")
        post_slug = slug.strip() if slug.strip() else None
        post_description = description.strip() if description.strip() else None

        # Create the post
        created_post = post_service.create_post(
            title=title,
            content=content,
            date=parsed_date,
            slug=post_slug,
            tags=post_tags,
            draft=is_draft,
            description=post_description
        )

        logger.info(f"Post created via HTMX by user {user['username']}: {created_post.frontmatter.title}")

        # Return success fragment with reload instruction
        success_html = f'''
        <div class="alert alert-success" hx-swap-oob="true" id="success-container">
            <p>Post "{created_post.frontmatter.title}" created successfully!</p>
        </div>
        <script>
            setTimeout(() => window.location.href = "/dashboard/posts", 1000);
        </script>
        '''

        return HTMLResponse(content=success_html, status_code=201)

    except PostValidationError as e:
        logger.error(f"Post validation error in HTMX create: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Validation error: {str(e)}"),
            status_code=422
        )
    except PostFileError as e:
        logger.error(f"Post file error in HTMX create: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"File error: {str(e)}"),
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error creating post via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while creating the post"),
            status_code=500
        )


@router.put("/posts/{slug}", response_class=HTMLResponse)
async def update_post_htmx(
    request: Request,
    slug: str,
    title: str = Form(...),
    content: str = Form(...),
    new_slug: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    post_date: str = Form(""),
    draft: str = Form("false")
):
    """
    Update an existing post via HTMX API.

    Args:
        slug: Current slug of the post to update

    Returns:
        HTML fragment with success message or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get post service
        post_service = get_post_service()

        # Parse form data (same logic as dashboard.py)
        parsed_date = datetime.fromisoformat(post_date).date() if post_date else None
        post_tags = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        is_draft = draft.lower() in ("true", "1", "yes", "on")
        updated_slug = new_slug.strip() if new_slug.strip() else None
        post_description = description.strip() if description.strip() else None

        # Update the post
        updated_post = post_service.update_post(
            slug=slug,
            title=title,
            content=content,
            date=parsed_date,
            new_slug=updated_slug,
            tags=post_tags,
            draft=is_draft,
            description=post_description
        )

        logger.info(f"Post updated via HTMX by user {user['username']}: {updated_post.frontmatter.title}")

        # Return success fragment with reload instruction
        success_html = f'''
        <div class="alert alert-success" hx-swap-oob="true" id="success-container">
            <p>Post "{updated_post.frontmatter.title}" updated successfully!</p>
        </div>
        <script>
            setTimeout(() => window.location.href = "/dashboard/posts", 1000);
        </script>
        '''

        return HTMLResponse(content=success_html, status_code=200)

    except PostNotFoundError as e:
        logger.error(f"Post not found in HTMX update: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Post not found: {str(e)}"),
            status_code=404
        )
    except PostValidationError as e:
        logger.error(f"Post validation error in HTMX update: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Validation error: {str(e)}"),
            status_code=422
        )
    except PostFileError as e:
        logger.error(f"Post file error in HTMX update: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"File error: {str(e)}"),
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error updating post via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while updating the post"),
            status_code=500
        )


@router.delete("/posts/{slug}", response_class=HTMLResponse)
async def delete_post_htmx(request: Request, slug: str):
    """
    Delete a post via HTMX API.

    Args:
        slug: Slug of the post to delete

    Returns:
        HTML fragment with success message or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get post service
        post_service = get_post_service()

        # Get the post first to capture title for logging
        try:
            post = post_service.get_post_by_slug(slug)
            post_title = post.frontmatter.title
        except PostNotFoundError:
            return HTMLResponse(
                content=_create_error_fragment(f"Post '{slug}' not found"),
                status_code=404
            )

        # Delete the post
        deleted = post_service.delete_post(slug)

        if deleted:
            logger.info(f"Post deleted via HTMX by user {user['username']}: {post_title}")

            # Return success fragment with reload instruction
            success_html = f'''
            <div class="alert alert-success" hx-swap-oob="true" id="success-container">
                <p>Post "{post_title}" deleted successfully!</p>
            </div>
            <script>
                setTimeout(() => window.location.reload(), 1000);
            </script>
            '''

            return HTMLResponse(content=success_html, status_code=200)
        else:
            return HTMLResponse(
                content=_create_error_fragment(f"Failed to delete post '{slug}'"),
                status_code=500
            )

    except Exception as e:
        logger.error(f"Unexpected error deleting post via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while deleting the post"),
            status_code=500
        )


@router.post("/posts/{slug}/publish", response_class=HTMLResponse)
async def publish_post_htmx(request: Request, slug: str):
    """
    Publish a post (set draft=False) via HTMX API.

    Args:
        slug: Post slug

    Returns:
        HTML fragment with success message or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get post service
        post_service = get_post_service()

        # Publish the post
        published_post = post_service.publish_post(slug)

        logger.info(f"Post published via HTMX by user {user['username']}: {published_post.frontmatter.title}")

        # Return success fragment with reload instruction
        success_html = f'''
        <div class="alert alert-success" hx-swap-oob="true" id="success-container">
            <p>Post "{published_post.frontmatter.title}" published successfully!</p>
        </div>
        <script>
            setTimeout(() => window.location.reload(), 1000);
        </script>
        '''

        return HTMLResponse(content=success_html, status_code=200)

    except PostNotFoundError as e:
        logger.error(f"Post not found for publish: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Post not found: {str(e)}"),
            status_code=404
        )
    except PostValidationError as e:
        logger.error(f"Post validation error in publish: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Error: {str(e)}"),
            status_code=422
        )
    except Exception as e:
        logger.error(f"Unexpected error publishing post via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while publishing the post"),
            status_code=500
        )


@router.post("/posts/{slug}/unpublish", response_class=HTMLResponse)
async def unpublish_post_htmx(request: Request, slug: str):
    """
    Unpublish a post (set draft=True) via HTMX API.

    Args:
        slug: Post slug

    Returns:
        HTML fragment with success message or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get post service
        post_service = get_post_service()

        # Unpublish the post
        unpublished_post = post_service.unpublish_post(slug)

        logger.info(f"Post unpublished via HTMX by user {user['username']}: {unpublished_post.frontmatter.title}")

        # Return success fragment with reload instruction
        success_html = f'''
        <div class="alert alert-success" hx-swap-oob="true" id="success-container">
            <p>Post "{unpublished_post.frontmatter.title}" unpublished successfully!</p>
        </div>
        <script>
            setTimeout(() => window.location.reload(), 1000);
        </script>
        '''

        return HTMLResponse(content=success_html, status_code=200)

    except PostNotFoundError as e:
        logger.error(f"Post not found for unpublish: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Post not found: {str(e)}"),
            status_code=404
        )
    except Exception as e:
        logger.error(f"Unexpected error unpublishing post via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while unpublishing the post"),
            status_code=500
        )


@router.post("/preview", response_class=HTMLResponse)
async def preview_markdown_htmx(
    request: Request,
    content: str = Form(...)
):
    """
    Preview markdown content as HTML via HTMX API.

    Args:
        content: Raw markdown content to preview

    Returns:
        HTML fragment with rendered markdown
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get markdown processor
        markdown_processor = get_markdown_processor()

        # Process the markdown content
        if not content.strip():
            # Return empty preview for empty content
            return HTMLResponse(content="<p><em>Start typing to see a preview...</em></p>", status_code=200)

        html_content = markdown_processor.process_markdown_text(content)

        logger.debug(f"Markdown preview generated for user {user['username']}")

        return HTMLResponse(content=html_content, status_code=200)

    except MarkdownProcessingError as e:
        logger.error(f"Markdown processing error in preview: {e}")
        return HTMLResponse(
            content=f"<div class='error-preview'><p><strong>Preview Error:</strong> {str(e)}</p></div>",
            status_code=200  # Return 200 to allow HTMX to display the error
        )
    except Exception as e:
        logger.error(f"Unexpected error in markdown preview: {e}")
        return HTMLResponse(
            content="<div class='error-preview'><p><strong>Preview Error:</strong> Unable to generate preview</p></div>",
            status_code=200  # Return 200 to allow HTMX to display the error
        )
