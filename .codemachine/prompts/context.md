# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T6",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Integrate build system with CLI tool, adding build command with options for watch mode, verbose output, and configuration override. Implement build status reporting.",
  "agent_type_hint": "BackendAgent",
  "inputs": "CLI framework, build system integration, command-line interface requirements",
  "target_files": ["microblog/cli.py"],
  "input_files": ["microblog/cli.py", "microblog/builder/generator.py"],
  "deliverables": "CLI build command, watch mode, verbose output, configuration options",
  "acceptance_criteria": "`microblog build` generates site successfully, watch mode rebuilds on changes, verbose output shows progress, build status reported",
  "dependencies": ["I3.T5"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: core-architecture (from 01_Plan_Overview_and_Setup.md)

```markdown
## 2. Core Architecture

*   **Architectural Style:** Hybrid Static-First Architecture with Layered Monolith for Management
*   **Technology Stack:**
    *   Frontend: HTMX 1.9+ (vendored), Pico.css (<10KB), Vanilla JavaScript (minimal)
    *   Backend: FastAPI 0.100+, Python 3.10+, Uvicorn ASGI server
    *   Database: SQLite3 (Python stdlib) for single user authentication
    *   Template Engine: Jinja2 for HTML generation and dashboard rendering
    *   Markdown: python-markdown + pymdown-extensions for content processing
    *   Authentication: python-jose + passlib[bcrypt] for JWT and password hashing
    *   CLI: Click for command-line interface and management tools
    *   File Watching: watchfiles for development mode configuration hot-reload
    *   Deployment: Docker-ready, systemd service, nginx/Caddy reverse proxy support
*   **Key Components/Services:**
    *   **Authentication Service**: JWT-based single-user authentication with bcrypt password hashing
    *   **Content Management Service**: CRUD operations for posts with markdown processing and validation
    *   **Static Site Generator**: Template rendering and asset copying with atomic build process
    *   **Dashboard Web Application**: HTMX-enhanced interface for content management and live preview
    *   **Image Management Service**: Upload, validation, and organization of media files
    *   **Build Management Service**: Orchestrates site generation with backup and rollback capabilities
    *   **CLI Interface**: Commands for build, serve, user creation, and system management
    *   **Configuration Manager**: YAML-based settings with validation and hot-reload support
    *   *(Component Diagram planned - see Iteration 1.T2)*
```

### Context: directory-structure (from 01_Plan_Overview_and_Setup.md)

```markdown
## 3. Directory Structure

*   **Root Directory:** `microblog/`
*   **Structure Definition:** Organized for clear separation of concerns with dedicated locations for source code, templates, content, and generated artifacts.

~~~
microblog/
├── microblog/                      # Main Python package
│   ├── __init__.py
│   ├── builder/                    # Static site generation
│   │   ├── __init__.py
│   │   ├── generator.py            # Main build orchestration
│   │   ├── markdown_processor.py   # Markdown parsing and frontmatter
│   │   ├── template_renderer.py    # Jinja2 template rendering
│   │   └── asset_manager.py        # Image and static file copying
│   ├── server/                     # Web application and dashboard
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI application setup
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── dashboard.py        # Dashboard page routes
│   │   │   └── api.py              # HTMX API endpoints
│   │   ├── middleware.py           # Auth and CSRF middleware
│   │   ├── models.py               # Pydantic request/response models
│   │   └── config.py               # Configuration management
│   ├── auth/                       # Authentication and user management
│   │   ├── __init__.py
│   │   ├── models.py               # User SQLite model
│   │   ├── jwt_handler.py          # JWT token management
│   │   └── password.py             # Password hashing utilities
│   ├── content/                    # Content management services
│   │   ├── __init__.py
│   │   ├── post_service.py         # Post CRUD operations
│   │   ├── image_service.py        # Image upload and management
│   │   └── validators.py           # Content validation logic
│   ├── cli.py                      # Click-based CLI interface
│   └── utils.py                    # Shared utilities and helpers
```

### Context: task-i3-t6 (from 02_Iteration_I3.md)

```markdown
    <!-- anchor: task-i3-t6 -->
    *   **Task 3.6:**
        *   **Task ID:** `I3.T6`
        *   **Description:** Integrate build system with CLI tool, adding build command with options for watch mode, verbose output, and configuration override. Implement build status reporting.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** CLI framework, build system integration, command-line interface requirements
        *   **Input Files:** ["microblog/cli.py", "microblog/builder/generator.py"]
        *   **Target Files:** ["microblog/cli.py"]
        *   **Deliverables:** CLI build command, watch mode, verbose output, configuration options
        *   **Acceptance Criteria:** `microblog build` generates site successfully, watch mode rebuilds on changes, verbose output shows progress, build status reported
        *   **Dependencies:** `I3.T5`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/cli.py`
    *   **Summary:** Contains a Click-based CLI framework with placeholder build command that currently only prints messages. Has existing patterns for verbose output, context passing, and command structure.
    *   **Recommendation:** You MUST enhance the existing `build()` function at lines 48-67 to integrate with the build generator. The CLI already has proper Click decorators, context handling, and verbose flag support - reuse these patterns.

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** Comprehensive build generator with atomic operations, progress tracking, backup/rollback, and detailed error handling. Provides `build_site()` function and `BuildGenerator` class with progress callbacks.
    *   **Recommendation:** You MUST import and use the `build_site()` function from this module (line 711). The progress callback mechanism (lines 87, 695) is perfect for implementing verbose output and build status reporting.

*   **File:** `microblog/utils.py`
    *   **Summary:** Contains utility functions for path management including `get_project_root()`, `get_content_dir()`, and `get_build_dir()`.
    *   **Recommendation:** You SHOULD use the existing path utilities rather than hardcoding paths. These are already imported in the CLI module.

*   **File:** `microblog/server/config.py`
    *   **Summary:** Configuration management system with hot-reload support using watchfiles library. Defines configuration models including BuildConfig.
    *   **Recommendation:** You SHOULD import and use the configuration system for configuration override functionality. The watchfiles library is already available for implementing watch mode.

### Implementation Tips & Notes

*   **Tip:** The CLI module already imports Click and has established patterns for context passing (`@click.pass_context`) and verbose handling (`ctx.obj.get("verbose", False)`). Follow these existing patterns for consistency.

*   **Tip:** The build generator has comprehensive progress reporting via `BuildProgress` objects and callbacks. Use this for implementing verbose output - you can create a progress callback function that prints status updates when verbose mode is enabled.

*   **Note:** The build command placeholder at line 61 says "TODO: Implement actual build logic in future iterations" - this is exactly what you need to replace with actual build system integration.

*   **Note:** The CLI already has a `--force` flag for the build command. You should integrate this with the build generator's force rebuild capability.

*   **Warning:** The existing CLI module has a global verbose flag that gets stored in the Click context. Make sure your new build options work with this existing pattern rather than conflicting with it.

*   **Tip:** For watch mode implementation, the project already uses `watchfiles` library (imported in config.py). You can use this same library to watch for content changes and trigger rebuilds.

*   **Note:** The current CLI has `serve`, `create-user`, `init`, and `status` commands. Your enhanced build command should follow the same style and error handling patterns as these existing commands.