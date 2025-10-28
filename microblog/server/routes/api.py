"""
HTMX API endpoints for dynamic post operations.

This module provides API endpoints optimized for HTMX interactions, returning
HTML fragments instead of JSON responses for seamless frontend integration.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from microblog.builder.markdown_processor import (
    MarkdownProcessingError,
    get_markdown_processor,
)
from microblog.content.image_service import (
    ImageUploadError,
    ImageValidationError,
    get_image_service,
)
from microblog.content.post_service import (
    PostFileError,
    PostNotFoundError,
    PostValidationError,
    get_post_service,
)
from microblog.content.tag_service import get_tag_service
from microblog.server.build_service import get_build_service
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


@router.post("/images/upload", response_class=HTMLResponse)
async def upload_image_htmx(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload an image file via HTMX API.

    Args:
        file: Uploaded image file

    Returns:
        HTML fragment with success message and markdown snippet or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        if not file.filename:
            return HTMLResponse(
                content=_create_error_fragment("No file selected"),
                status_code=422
            )

        # Check if file has content
        file_content = await file.read()
        if not file_content:
            return HTMLResponse(
                content=_create_error_fragment("Uploaded file is empty"),
                status_code=422
            )

        # Reset file pointer
        await file.seek(0)

        # Get image service
        image_service = get_image_service()

        # Save the uploaded file
        result = await image_service.save_uploaded_file_async(file.file, file.filename)

        logger.info(f"Image uploaded via HTMX by user {user['username']}: {result['filename']}")

        # Return success fragment with markdown snippet and file info
        success_html = f'''
        <div class="alert alert-success" hx-swap-oob="true" id="success-container">
            <p>Image "{result['filename']}" uploaded successfully!</p>
            <div class="upload-result mt-2">
                <p><strong>Markdown snippet:</strong></p>
                <div class="code-block">
                    <code>{result['markdown']}</code>
                    <button type="button" class="btn btn-sm btn-outline-secondary ms-2"
                            onclick="navigator.clipboard.writeText('{result['markdown']}')">
                        Copy
                    </button>
                </div>
                <p class="text-muted mt-2">
                    File size: {result['size']:,} bytes |
                    URL: <code>{result['url']}</code>
                </p>
            </div>
        </div>
        <div hx-swap-oob="innerHTML:#file-input-container">
            <input type="file"
                   class="form-control"
                   name="file"
                   accept="image/*"
                   hx-post="/api/images/upload"
                   hx-encoding="multipart/form-data"
                   hx-indicator="#upload-indicator">
            <div class="form-text">
                Supported formats: JPG, PNG, GIF, SVG, WebP, ICO, BMP (max 50MB)
            </div>
        </div>
        '''

        return HTMLResponse(content=success_html, status_code=201)

    except ImageValidationError as e:
        logger.error(f"Image validation error in upload: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Validation error: {str(e)}"),
            status_code=422
        )
    except ImageUploadError as e:
        logger.error(f"Image upload error: {e}")
        return HTMLResponse(
            content=_create_error_fragment(f"Upload error: {str(e)}"),
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading image via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while uploading the image"),
            status_code=500
        )


@router.get("/images", response_class=HTMLResponse)
async def list_images_htmx(request: Request):
    """
    List uploaded images via HTMX API.

    Returns:
        HTML fragment with image gallery
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # Get image service
        image_service = get_image_service()
        images = image_service.list_images()

        # Generate image gallery HTML
        if not images:
            gallery_html = '<p class="text-muted">No images uploaded yet.</p>'
        else:
            gallery_items = []
            for image in images:
                # Format file size
                size_mb = image['size'] / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{image['size'] / 1024:.1f} KB"

                gallery_items.append(f'''
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">{image['filename']}</h6>
                            <p class="card-text">
                                <small class="text-muted">
                                    Size: {size_str}<br>
                                    URL: <code>{image['url']}</code>
                                </small>
                            </p>
                            <div class="btn-group w-100">
                                <button type="button" class="btn btn-sm btn-outline-primary"
                                        onclick="navigator.clipboard.writeText('![{image['filename']}]({image['url']})')">
                                    Copy Markdown
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary"
                                        onclick="navigator.clipboard.writeText('{image['url']}')">
                                    Copy URL
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                ''')

            gallery_html = f'''
            <div class="row">
                {''.join(gallery_items)}
            </div>
            '''

        logger.debug(f"Image gallery requested by user {user['username']}")

        return HTMLResponse(content=gallery_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error listing images via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while loading images"),
            status_code=500
        )


@router.post("/build", response_class=HTMLResponse)
async def trigger_build_htmx(request: Request):
    """
    Trigger a site build via HTMX API.

    Returns:
        HTML fragment with build status or error details
    """
    try:
        # Require authentication
        user = require_authentication(request)

        # CSRF validation is handled by middleware for /api/ paths

        # Get build service
        build_service = get_build_service()

        # Queue the build
        try:
            job_id = build_service.queue_build(user_id=user.get('username'))
            logger.info(f"Build triggered via HTMX by user {user['username']}: job {job_id}")

            # Return success fragment with build status
            success_html = f'''
            <div class="alert alert-info" hx-swap-oob="true" id="build-status">
                <p><strong>Build Queued</strong></p>
                <p>Your build has been added to the queue. Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="build-details">
                    <small class="text-muted">Status: Queued</small>
                </div>
            </div>
            <div hx-get="/api/build/{job_id}/status"
                 hx-trigger="every 1s"
                 hx-target="#build-status"
                 hx-swap="outerHTML">
            </div>
            '''

            return HTMLResponse(content=success_html, status_code=202)

        except RuntimeError as e:
            return HTMLResponse(
                content=_create_error_fragment(f"Build queue error: {str(e)}"),
                status_code=429
            )

    except Exception as e:
        logger.error(f"Unexpected error triggering build via HTMX: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while triggering the build"),
            status_code=500
        )


@router.get("/build/{job_id}/status", response_class=HTMLResponse)
async def get_build_status_htmx(request: Request, job_id: str):
    """
    Get build status for a specific job via HTMX API.

    Args:
        job_id: Build job ID

    Returns:
        HTML fragment with current build status
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get build service
        build_service = get_build_service()

        # Get job status
        job = build_service.get_job_status(job_id)
        if not job:
            return HTMLResponse(
                content=_create_error_fragment(f"Build job {job_id} not found"),
                status_code=404
            )

        # Generate status HTML based on job state
        if job.status.value == "queued":
            queue_position = len([j for j in build_service.get_build_queue() if j.created_at <= job.created_at])
            status_html = f'''
            <div class="alert alert-info" id="build-status">
                <p><strong>Build Queued</strong></p>
                <p>Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="build-details">
                    <small class="text-muted">Position in queue: {queue_position}</small>
                </div>
            </div>
            <div hx-get="/api/build/{job_id}/status"
                 hx-trigger="every 1s"
                 hx-target="#build-status"
                 hx-swap="outerHTML">
            </div>
            '''

        elif job.status.value == "running":
            progress = job.current_progress
            if progress:
                progress_percent = progress.percentage
                phase_name = progress.phase.value.replace('_', ' ').title()
                progress_message = progress.message
            else:
                progress_percent = 0
                phase_name = "Starting"
                progress_message = "Build is starting..."

            status_html = f'''
            <div class="alert alert-primary" id="build-status">
                <p><strong>Build Running</strong></p>
                <p>Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                         role="progressbar"
                         style="width: {progress_percent}%"
                         aria-valuenow="{progress_percent}"
                         aria-valuemin="0"
                         aria-valuemax="100">
                        {progress_percent:.1f}%
                    </div>
                </div>
                <div class="build-details">
                    <p class="mb-1"><strong>Phase:</strong> {phase_name}</p>
                    <small class="text-muted">{progress_message}</small>
                </div>
            </div>
            <div hx-get="/api/build/{job_id}/status"
                 hx-trigger="every 1s"
                 hx-target="#build-status"
                 hx-swap="outerHTML">
            </div>
            '''

        elif job.status.value == "completed":
            duration = job.result.duration if job.result else 0
            stats_html = ""
            if job.result and job.result.stats:
                stats = job.result.stats
                stats_items = []
                if 'content' in stats:
                    stats_items.append(f"Posts: {stats['content'].get('processed_posts', 0)}")
                if 'rendering' in stats:
                    stats_items.append(f"Pages: {stats['rendering'].get('pages_rendered', 0)}")
                if 'assets' in stats:
                    stats_items.append(f"Assets: {stats['assets'].get('total_successful', 0)}")
                if stats_items:
                    stats_html = f"<small class='text-muted'>{' | '.join(stats_items)}</small>"

            status_html = f'''
            <div class="alert alert-success" id="build-status">
                <p><strong>Build Completed Successfully!</strong></p>
                <p>Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar bg-success" role="progressbar" style="width: 100%">100%</div>
                </div>
                <div class="build-details">
                    <p class="mb-1">Completed in {duration:.1f} seconds</p>
                    {stats_html}
                </div>
                <button class="btn btn-sm btn-outline-secondary mt-2"
                        hx-get="/api/build/recent"
                        hx-target="#build-status"
                        hx-swap="outerHTML">
                    View Recent Builds
                </button>
            </div>
            '''

        elif job.status.value == "failed":
            error_message = job.error_message or "Unknown error"
            duration = job.result.duration if job.result else 0

            status_html = f'''
            <div class="alert alert-danger" id="build-status">
                <p><strong>Build Failed</strong></p>
                <p>Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar bg-danger" role="progressbar" style="width: 100%">Failed</div>
                </div>
                <div class="build-details">
                    <p class="mb-1"><strong>Error:</strong> {error_message}</p>
                    <small class="text-muted">Failed after {duration:.1f} seconds</small>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-2"
                        hx-post="/api/build"
                        hx-target="#build-status"
                        hx-swap="outerHTML">
                    Retry Build
                </button>
            </div>
            '''

        else:  # cancelled
            status_html = f'''
            <div class="alert alert-warning" id="build-status">
                <p><strong>Build Cancelled</strong></p>
                <p>Job ID: <code>{job_id}</code></p>
                <div class="progress mb-2">
                    <div class="progress-bar bg-warning" role="progressbar" style="width: 0%">Cancelled</div>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-2"
                        hx-post="/api/build"
                        hx-target="#build-status"
                        hx-swap="outerHTML">
                    Start New Build
                </button>
            </div>
            '''

        return HTMLResponse(content=status_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error getting build status for job {job_id}: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while getting build status"),
            status_code=500
        )


@router.get("/build/recent", response_class=HTMLResponse)
async def get_recent_builds_htmx(request: Request):
    """
    Get recent builds via HTMX API.

    Returns:
        HTML fragment with recent build history
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get build service
        build_service = get_build_service()

        # Get recent builds
        recent_builds = build_service.get_recent_builds(limit=5)

        if not recent_builds:
            history_html = '''
            <div class="alert alert-info" id="build-status">
                <p><strong>No Recent Builds</strong></p>
                <p>No build history available.</p>
                <button class="btn btn-sm btn-outline-primary mt-2"
                        hx-post="/api/build"
                        hx-target="#build-status"
                        hx-swap="outerHTML">
                    Start First Build
                </button>
            </div>
            '''
        else:
            build_items = []
            for job in recent_builds:
                status_class = "success" if job.status.value == "completed" else "danger"
                status_text = "✓" if job.status.value == "completed" else "✗"
                duration = job.result.duration if job.result else 0

                build_items.append(f'''
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <div>
                        <span class="badge bg-{status_class}">{status_text}</span>
                        <code class="ms-2">{job.job_id[:8]}...</code>
                        <small class="text-muted ms-2">
                            {job.completed_at.strftime("%Y-%m-%d %H:%M:%S") if job.completed_at else "Unknown"}
                        </small>
                    </div>
                    <div>
                        <small class="text-muted">{duration:.1f}s</small>
                    </div>
                </div>
                ''')

            history_html = f'''
            <div class="card" id="build-status">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Recent Builds</h6>
                    <button class="btn btn-sm btn-outline-primary"
                            hx-post="/api/build"
                            hx-target="#build-status"
                            hx-swap="outerHTML">
                        New Build
                    </button>
                </div>
                <div class="card-body">
                    <div class="build-history">
                        {''.join(build_items)}
                    </div>
                </div>
            </div>
            '''

        return HTMLResponse(content=history_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error getting recent builds: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while loading recent builds"),
            status_code=500
        )


@router.get("/build/queue", response_class=HTMLResponse)
async def get_build_queue_htmx(request: Request):
    """
    Get build queue status via HTMX API.

    Returns:
        HTML fragment with current build queue
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get build service
        build_service = get_build_service()

        # Get current build and queue
        current_build = build_service.get_current_build()
        queued_builds = build_service.get_build_queue()

        queue_html = '<div class="card" id="build-queue">'
        queue_html += '<div class="card-header"><h6 class="mb-0">Build Queue Status</h6></div>'
        queue_html += '<div class="card-body">'

        if current_build:
            progress = current_build.current_progress
            if progress:
                progress_percent = progress.percentage
                phase_name = progress.phase.value.replace('_', ' ').title()
            else:
                progress_percent = 0
                phase_name = "Starting"

            queue_html += f'''
            <div class="mb-3">
                <h6 class="text-primary">Currently Building</h6>
                <div class="d-flex justify-content-between align-items-center">
                    <code>{current_build.job_id[:8]}...</code>
                    <small class="text-muted">{phase_name}</small>
                </div>
                <div class="progress mt-1">
                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                         style="width: {progress_percent}%"></div>
                </div>
            </div>
            '''

        if queued_builds:
            queue_html += '<h6 class="text-info">Queued Builds</h6>'
            for i, job in enumerate(queued_builds):
                queue_html += f'''
                <div class="d-flex justify-content-between align-items-center py-1">
                    <div>
                        <span class="badge bg-secondary">{i + 1}</span>
                        <code class="ms-2">{job.job_id[:8]}...</code>
                    </div>
                    <small class="text-muted">{job.created_at.strftime("%H:%M:%S")}</small>
                </div>
                '''
        else:
            if not current_build:
                queue_html += '<p class="text-muted mb-0">No builds queued or running.</p>'

        queue_html += '</div></div>'

        return HTMLResponse(content=queue_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error getting build queue: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while loading build queue"),
            status_code=500
        )


@router.get("/tags/autocomplete", response_class=HTMLResponse)
async def get_tag_autocomplete_htmx(request: Request, q: str = ""):
    """
    Get tag autocomplete suggestions via HTMX API.

    Args:
        q: Query string for tag autocomplete

    Returns:
        HTML fragment with tag suggestions
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get tag service
        tag_service = get_tag_service()

        # Get suggestions
        suggestions = tag_service.get_tag_suggestions(q, limit=10, include_drafts=True)

        if not suggestions:
            return HTMLResponse(content="", status_code=200)

        # Generate autocomplete HTML
        suggestion_items = []
        for suggestion in suggestions:
            tag = suggestion['tag']
            count = suggestion['count']
            exact_match = suggestion.get('exact_match', False)
            css_class = "autocomplete-exact" if exact_match else "autocomplete-suggestion"

            # Escape single quotes for JavaScript
            escaped_tag = tag.replace("'", "\\'")
            suggestion_items.append(f'''
            <div class="{css_class}"
                 onclick="selectTag('{escaped_tag}')">
                <span class="tag-name">{tag}</span>
                <span class="tag-count">({count})</span>
            </div>
            ''')

        autocomplete_html = f'''
        <div class="tag-autocomplete-dropdown" id="tag-autocomplete">
            {''.join(suggestion_items)}
        </div>
        '''

        return HTMLResponse(content=autocomplete_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error in tag autocomplete: {e}")
        return HTMLResponse(content="", status_code=200)


@router.get("/tags", response_class=HTMLResponse)
async def get_all_tags_htmx(request: Request, include_drafts: str = "true"):
    """
    Get all tags with usage statistics via HTMX API.

    Args:
        include_drafts: Whether to include tags from draft posts

    Returns:
        HTML fragment with tag list and statistics
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get tag service
        tag_service = get_tag_service()
        include_drafts_bool = include_drafts.lower() in ("true", "1", "yes")

        # Get all tags and statistics
        all_tags = tag_service.get_all_tags(include_drafts=include_drafts_bool)
        stats = tag_service.get_tag_stats(include_drafts=include_drafts_bool)

        # Generate tags HTML
        if not all_tags:
            tags_html = '''
            <div class="alert alert-info">
                <p>No tags found. Start adding tags to your posts to see them here!</p>
            </div>
            '''
        else:
            tag_items = []
            for tag in all_tags:
                usage_count = stats['most_used_tags'].get(tag, 0)
                tag_items.append(f'''
                <div class="tag-item d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div class="tag-info">
                        <span class="tag-name fw-bold">{tag}</span>
                        <small class="text-muted ms-2">Used {usage_count} time{'s' if usage_count != 1 else ''}</small>
                    </div>
                    <div class="tag-actions">
                        <button class="btn btn-sm btn-outline-primary"
                                hx-get="/api/posts/filter?tag={tag}&include_drafts={include_drafts}"
                                hx-target="#posts-container"
                                hx-swap="innerHTML">
                            View Posts
                        </button>
                    </div>
                </div>
                ''')

            # Statistics summary
            stats_html = f'''
            <div class="tag-stats mb-3 p-3 bg-light rounded">
                <h6>Tag Statistics</h6>
                <div class="row text-center">
                    <div class="col">
                        <strong>{stats['unique_tags']}</strong><br>
                        <small class="text-muted">Unique Tags</small>
                    </div>
                    <div class="col">
                        <strong>{stats['tagged_posts']}</strong><br>
                        <small class="text-muted">Tagged Posts</small>
                    </div>
                    <div class="col">
                        <strong>{stats['avg_tags_per_post']}</strong><br>
                        <small class="text-muted">Avg per Post</small>
                    </div>
                </div>
            </div>
            '''

            tags_html = f'''
            {stats_html}
            <div class="tag-list">
                {''.join(tag_items)}
            </div>
            '''

        return HTMLResponse(content=tags_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error getting all tags: {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while loading tags"),
            status_code=500
        )


@router.get("/posts/filter", response_class=HTMLResponse)
async def filter_posts_by_tag_htmx(request: Request, tag: str = "", include_drafts: str = "false"):
    """
    Filter posts by tag via HTMX API.

    Args:
        tag: Tag to filter by
        include_drafts: Whether to include draft posts

    Returns:
        HTML fragment with filtered posts
    """
    try:
        # Require authentication
        require_authentication(request)

        # Get post service
        post_service = get_post_service()
        include_drafts_bool = include_drafts.lower() in ("true", "1", "yes")

        # Get filtered posts
        if tag:
            posts = post_service.list_posts(
                include_drafts=include_drafts_bool,
                tag_filter=tag
            )
            title = f'Posts tagged with "{tag}"'
        else:
            posts = post_service.list_posts(include_drafts=include_drafts_bool)
            title = "All Posts"

        # Generate posts HTML
        if not posts:
            if tag:
                posts_html = f'''
                <div class="alert alert-info">
                    <p>No posts found with tag "{tag}".</p>
                    <button class="btn btn-sm btn-outline-secondary"
                            hx-get="/api/posts/filter?include_drafts={include_drafts}"
                            hx-target="#posts-container"
                            hx-swap="innerHTML">
                        Show All Posts
                    </button>
                </div>
                '''
            else:
                posts_html = '''
                <div class="alert alert-info">
                    <p>No posts found.</p>
                </div>
                '''
        else:
            post_items = []
            for post in posts:
                status_badge = "Draft" if post.is_draft else "Published"
                status_class = "secondary" if post.is_draft else "success"
                tags_display = ", ".join(post.frontmatter.tags) if post.frontmatter.tags else "No tags"

                post_items.append(f'''
                <div class="post-item card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title mb-1">
                                <a href="/dashboard/posts/{post.computed_slug}/edit"
                                   class="text-decoration-none">{post.frontmatter.title}</a>
                            </h5>
                            <span class="badge bg-{status_class}">{status_badge}</span>
                        </div>

                        {f'<p class="card-text text-muted">{post.frontmatter.description}</p>' if post.frontmatter.description else ''}

                        <div class="post-meta">
                            <small class="text-muted">
                                <strong>Date:</strong> {post.frontmatter.date.strftime('%Y-%m-%d')} |
                                <strong>Tags:</strong> {tags_display}
                            </small>
                        </div>

                        <div class="post-actions mt-2">
                            <div class="btn-group">
                                <a href="/dashboard/posts/{post.computed_slug}/edit"
                                   class="btn btn-sm btn-outline-primary">Edit</a>
                                <button class="btn btn-sm btn-outline-secondary"
                                        hx-get="/preview/{post.computed_slug}"
                                        hx-target="#preview-modal-body"
                                        hx-swap="innerHTML"
                                        data-bs-toggle="modal"
                                        data-bs-target="#previewModal">
                                    Preview
                                </button>
                                {'<button class="btn btn-sm btn-outline-success" hx-post="/api/posts/' + post.computed_slug + '/publish" hx-target="#form-messages" hx-swap="innerHTML">Publish</button>' if post.is_draft else '<button class="btn btn-sm btn-outline-warning" hx-post="/api/posts/' + post.computed_slug + '/unpublish" hx-target="#form-messages" hx-swap="innerHTML">Unpublish</button>'}
                                <button class="btn btn-sm btn-outline-danger"
                                        hx-delete="/api/posts/{post.computed_slug}"
                                        hx-target="#form-messages"
                                        hx-swap="innerHTML"
                                        hx-confirm="Are you sure you want to delete this post?">
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                ''')

            # Header with filter info
            filter_header = f'''
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4>{title} ({len(posts)} post{'s' if len(posts) != 1 else ''})</h4>
                {f'<button class="btn btn-sm btn-outline-secondary" hx-get="/api/posts/filter?include_drafts={include_drafts}" hx-target="#posts-container" hx-swap="innerHTML">Clear Filter</button>' if tag else ''}
            </div>
            '''

            posts_html = f'''
            {filter_header}
            <div class="posts-list">
                {''.join(post_items)}
            </div>
            '''

        return HTMLResponse(content=posts_html, status_code=200)

    except Exception as e:
        logger.error(f"Unexpected error filtering posts by tag '{tag}': {e}")
        return HTMLResponse(
            content=_create_error_fragment("An unexpected error occurred while filtering posts"),
            status_code=500
        )
