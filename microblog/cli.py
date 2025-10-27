"""
Click-based CLI interface for microblog.

This module provides command-line tools for building, serving, and managing
the microblog application.
"""

import os
from pathlib import Path

import click

from microblog.auth.models import User
from microblog.database import (
    create_admin_user,
    get_database_path,
    setup_database_if_needed,
)
from microblog.utils import get_build_dir, get_content_dir, get_project_root


@click.group()
@click.version_option(version="0.1.0", prog_name="microblog")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """
    Microblog - A lightweight, self-hosted blogging platform.

    Generate static HTML sites from markdown content with a dynamic
    dashboard for content management.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo("Verbose mode enabled")


@main.command()
@click.option(
    "--output", "-o", default="build", help="Output directory for generated site"
)
@click.option(
    "--force", "-f", is_flag=True, help="Force rebuild even if no changes detected"
)
@click.pass_context
def build(ctx: click.Context, output: str, force: bool) -> None:
    """
    Build the static site from markdown content.

    Processes all markdown files in the content directory and generates
    a complete static HTML site.
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Building site to {output} directory...")
        click.echo(f"Force rebuild: {force}")

    # TODO: Implement actual build logic in future iterations
    click.echo("Build functionality will be implemented in the next iteration")
    click.echo(f"Would build site to: {Path(output).resolve()}")

    if force:
        click.echo("Force rebuild flag acknowledged")


@main.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind the server")
@click.option("--port", "-p", default=8000, type=int, help="Port to bind the server")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option(
    "--dashboard-only", is_flag=True, help="Serve only the dashboard (no static site)"
)
@click.pass_context
def serve(
    ctx: click.Context, host: str, port: int, reload: bool, dashboard_only: bool
) -> None:
    """
    Start the development server.

    Serves the generated static site and provides access to the
    management dashboard for content editing.
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Starting server on {host}:{port}")
        click.echo(f"Auto-reload: {reload}")
        click.echo(f"Dashboard only: {dashboard_only}")

    # TODO: Implement actual server logic in future iterations
    click.echo("Server functionality will be implemented in the next iteration")
    click.echo(f"Would serve on: http://{host}:{port}")

    if dashboard_only:
        click.echo("Dashboard-only mode acknowledged")

    if reload:
        click.echo("Auto-reload mode acknowledged")


@main.command()
@click.option("--username", "-u", prompt=True, help="Username for the blog admin")
@click.option(
    "--email",
    "-e",
    prompt=True,
    help="Email address for the blog admin"
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password for the blog admin",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing user if present")
@click.pass_context
def create_user(ctx: click.Context, username: str, email: str, password: str, force: bool) -> None:
    """
    Create a new admin user for the blog.

    This command creates the authentication credentials needed to
    access the management dashboard.
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Creating user: {username}")
        click.echo(f"Email: {email}")
        click.echo(f"Force overwrite: {force}")

    try:
        # Initialize database if needed
        if not setup_database_if_needed():
            click.echo(click.style("ERROR: Failed to initialize database", fg="red"))
            return

        db_path = get_database_path()

        # Handle existing user scenario
        if User.user_exists(db_path) and not force:
            click.echo(click.style("ERROR: Admin user already exists. Use --force to overwrite.", fg="red"))
            return

        # If force is enabled and user exists, we need to handle it
        # Note: Current User model doesn't support deletion, so we'll show a warning
        if User.user_exists(db_path) and force:
            click.echo(click.style("WARNING: Admin user already exists. Creating new user will fail due to database constraints.", fg="yellow"))
            click.echo("Consider using a different username or resetting the database.")

        # Create the admin user
        user = create_admin_user(username, email, password)

        if user:
            click.echo(click.style(f"SUCCESS: Admin user '{username}' created successfully!", fg="green"))
            if verbose:
                click.echo(f"User ID: {user.user_id}")
                click.echo(f"Role: {user.role}")
                click.echo(f"Created at: {user.created_at}")
        else:
            click.echo(click.style("ERROR: Failed to create user. User may already exist.", fg="red"))

    except ValueError as e:
        click.echo(click.style(f"VALIDATION ERROR: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"ERROR: {e}", fg="red"))
        if verbose:
            import traceback
            click.echo(traceback.format_exc())


@main.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """
    Initialize a new microblog project.

    Creates the necessary directory structure and configuration
    files for a new blog.
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("Initializing new microblog project...")

    # TODO: Implement actual initialization logic in future iterations
    click.echo("Project initialization will be implemented in the next iteration")
    click.echo("Would create:")
    click.echo("  - content/posts/")
    click.echo("  - content/pages/")
    click.echo("  - content/images/")
    click.echo("  - content/_data/config.yaml")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """
    Show the current status of the microblog project.

    Displays information about content, build status, and configuration.
    """
    verbose = ctx.obj.get("verbose", False)

    project_root = get_project_root()
    content_dir = get_content_dir()
    build_dir = get_build_dir()

    click.echo("Microblog Status")
    click.echo("=" * 40)
    click.echo(f"Project root: {project_root}")
    click.echo(f"Content directory: {content_dir}")
    click.echo(f"Build directory: {build_dir}")

    # Check if directories exist
    if content_dir.exists():
        posts_dir = content_dir / "posts"
        if posts_dir.exists():
            post_count = len(list(posts_dir.glob("*.md")))
            click.echo(f"Posts found: {post_count}")
        else:
            click.echo("Posts directory: Not found")
    else:
        click.echo("Content directory: Not found")

    if build_dir.exists():
        click.echo("Build directory: Exists")
    else:
        click.echo("Build directory: Not found")

    if verbose:
        click.echo(f"Python executable: {os.sys.executable}")
        click.echo(f"Working directory: {os.getcwd()}")


if __name__ == "__main__":
    main()
