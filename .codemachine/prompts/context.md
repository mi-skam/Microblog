# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T1",
  "iteration_id": "I1",
  "iteration_goal": "Establish project foundation, directory structure, core architecture documentation, and basic CLI framework",
  "description": "Initialize project structure, Python package setup, and basic CLI framework with Click. Create all necessary directories and files, set up pyproject.toml with dependencies, and implement basic CLI commands for build and serve operations.",
  "agent_type_hint": "SetupAgent",
  "inputs": "Project directory structure definition from Section 3, technology stack requirements from Section 2",
  "target_files": ["pyproject.toml", "requirements.txt", "microblog/__init__.py", "microblog/cli.py", "README.md", ".gitignore", "Makefile", "Dockerfile", "docker-compose.yml"],
  "input_files": [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"],
  "deliverables": "Complete Python package structure, installable CLI tool, dependency management setup, development environment configuration, basic documentation",
  "acceptance_criteria": "CLI tool installs successfully, `microblog --help` displays command structure, all directories created, dependencies resolve without conflicts, Docker setup functional",
  "dependencies": [],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

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
├── templates/                      # Jinja2 templates for site generation
│   ├── base.html                   # Base template with common structure
│   ├── index.html                  # Homepage template
│   ├── post.html                   # Individual post template
│   ├── archive.html                # Post listing/archive template
│   ├── tag.html                    # Tag-based post listing
│   ├── rss.xml                     # RSS feed template
│   └── dashboard/                  # Dashboard-specific templates
│       ├── layout.html             # Dashboard base template
│       ├── login.html              # Authentication form
│       ├── posts_list.html         # Post management interface
│       ├── post_edit.html          # Post creation/editing form
│       └── settings.html           # Configuration management
├── static/                         # Static assets for dashboard and site
│   ├── css/
│   │   ├── dashboard.css           # Dashboard-specific styles
│   │   └── site.css                # Public site styles (Pico.css based)
│   ├── js/
│   │   ├── htmx.min.js             # Vendored HTMX library
│   │   └── dashboard.js            # Minimal dashboard JavaScript
│   └── images/
│       └── favicon.ico             # Site favicon
├── docs/                           # Documentation and design artifacts
│   ├── diagrams/                   # UML diagrams (PlantUML source files)
│   │   ├── component_diagram.puml
│   │   ├── database_erd.puml
│   │   ├── auth_flow.puml
│   │   ├── build_process.puml
│   │   └── deployment.puml
│   ├── adr/                        # Architectural Decision Records
│   │   ├── 001-static-first-architecture.md
│   │   ├── 002-single-user-design.md
│   │   └── 003-full-rebuild-strategy.md
│   └── api/                        # API documentation
│       └── openapi.yaml            # OpenAPI v3 specification
├── content/                        # User content directory (runtime)
│   ├── posts/                      # Markdown blog posts
│   ├── pages/                      # Static pages (about, contact, etc.)
│   ├── images/                     # User-uploaded images
│   └── _data/
│       └── config.yaml             # Site configuration
├── build/                          # Generated static site (gitignored)
├── build.bak/                      # Build backup directory (gitignored)
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests for individual components
│   ├── integration/                # Integration tests for API endpoints
│   └── e2e/                        # End-to-end tests for workflows
├── scripts/                        # Deployment and utility scripts
│   ├── deploy.sh                   # Production deployment script
│   ├── backup.sh                   # Content backup script
│   └── dev-setup.sh                # Development environment setup
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container deployment
├── docker-compose.yml              # Local development with Docker
├── .gitignore                      # Git ignore rules
├── README.md                       # Project documentation
└── Makefile                        # Development shortcuts
~~~
```

### Context: technology-stack (from 02_Architecture_Overview.md)

```markdown
### 3.2. Technology Stack Summary

| **Component** | **Technology** | **Version** | **Justification** |
|---------------|----------------|-------------|-------------------|
| **Backend Language** | Python | 3.10+ | Excellent ecosystem for text processing, web frameworks, and CLI tools. Mature libraries for markdown, templating, and authentication. |
| **Web Framework** | FastAPI | 0.100+ | Modern async framework with automatic OpenAPI documentation, excellent type support, and built-in security features. Ideal for both API endpoints and traditional web pages. |
| **Template Engine** | Jinja2 | Latest | Industry standard with excellent performance, template inheritance, and extensive filter ecosystem. Native FastAPI integration. |
| **Markdown Processing** | python-markdown + pymdown-extensions | Latest | Comprehensive markdown parsing with syntax highlighting, tables, and extensible architecture for future enhancements. |
| **Frontmatter Parsing** | python-frontmatter | Latest | Reliable YAML frontmatter extraction with excellent error handling and validation capabilities. |
| **Authentication** | python-jose + passlib | Latest | Secure JWT implementation with bcrypt password hashing. Battle-tested libraries with comprehensive security features. |
| **Database** | SQLite3 | Python stdlib | Lightweight, serverless database perfect for single-user scenarios. No external dependencies or configuration required. |
| **Frontend Enhancement** | HTMX | 1.9+ (vendored) | Enables dynamic interactions without complex JavaScript frameworks. Maintains progressive enhancement principles. |
| **Styling** | Pico.css | Latest | Minimal, semantic CSS framework (<10KB) providing clean styling without design lock-in. |
| **CLI Framework** | Click | Latest | Robust command-line interface with excellent help generation, parameter validation, and nested command support. |
| **File Watching** | watchfiles | Latest | High-performance file system monitoring for development mode configuration reloading. |
| **Development Tools** | Ruff | Latest | Fast Python linter and formatter providing code quality enforcement and automatic formatting. |
| **Process Management** | Uvicorn | Latest | ASGI server with excellent performance, automatic reloading, and production deployment capabilities. |
```

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
*   **Data Model Overview:**
    *   **User**: Single admin user with credentials stored in SQLite (bcrypt hashed passwords)
    *   **Post**: Markdown files with YAML frontmatter containing title, date, slug, tags, draft status
    *   **Image**: Files stored in content/images/ with validation and build-time copying
    *   **Configuration**: YAML file with site settings, build options, server configuration, auth settings
    *   **Session**: Stateless JWT tokens in httpOnly cookies with configurable expiration
    *   *(Database ERD planned - see Iteration 1.T3)*
*   **API Contract Style:** RESTful HTTP API with HTMX enhancement for dynamic interactions, HTML-first responses for progressive enhancement
    *   *(Initial OpenAPI specification planned - see Iteration 2.T1)*
*   **Communication Patterns:**
    *   Synchronous HTTP request/response for page loads and API calls
    *   HTMX partial updates for dynamic content without full page refreshes
    *   File system events for configuration hot-reload in development mode
    *   Atomic file operations for build process with backup/rollback safety
    *   *(Key sequence diagrams planned - see Iteration 2.T2)*
```

### Context: project-overview (from 01_Plan_Overview_and_Setup.md)

```markdown
## 1. Project Overview

*   **Goal:** Develop a lightweight, self-hosted blogging platform that generates static HTML pages for performance while providing a dynamic HTMX-powered dashboard for content management.
*   **High-Level Requirements Summary:**
    *   Single-user authentication with JWT-based session management
    *   Markdown-based post creation and editing with YAML frontmatter
    *   Static site generation with full rebuild strategy (<5s for 100 posts)
    *   HTMX-enhanced dashboard for CRUD operations without full page refreshes
    *   Filesystem-based image storage with automatic build-time copying
    *   Tag-based content organization and RSS feed generation
    *   CLI tools for build, serve, and user management operations
    *   Build backup and atomic rollback mechanisms for reliability
    *   Configuration hot-reload in development mode
    *   Live markdown preview during content editing
*   **Key Assumptions:**
    *   Single-user design eliminates complex permission systems
    *   Content volume will not exceed 1,000 posts (performance tested)
    *   Users have basic familiarity with markdown syntax
    *   Full rebuild strategy is acceptable for target content volume
    *   Users will implement their own content backup strategy (Git recommended)
    *   Dashboard usage occurs on trusted networks (localhost or VPN)
    *   Images are pre-optimized before upload (no automatic compression)
    *   Filesystem has sufficient read/write permissions for operations
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `pyproject.toml`
    *   **Summary:** This file already exists and contains the correct Python package configuration with all required dependencies listed and properly configured.
    *   **Recommendation:** You SHOULD verify that all dependencies from the architecture manifest are present. The file appears complete with correct version constraints and includes development dependencies, scripts entry points, and tool configurations.

*   **File:** `microblog/__init__.py`
    *   **Summary:** Basic package initialization file with version information and package description.
    *   **Recommendation:** The file is properly set up with package metadata. You may need to ensure the version matches across all configuration files.

*   **File:** `microblog/cli.py`
    *   **Summary:** This file contains a well-structured Click-based CLI implementation with all the required commands (build, serve, create-user, init, status) but with placeholder implementations.
    *   **Recommendation:** The CLI structure is already correct and follows Click best practices. You MUST keep the existing command structure and option definitions as they align with the specification. The TODO comments indicate where future iterations will implement actual functionality.

*   **File:** `microblog/utils.py`
    *   **Summary:** Contains utility functions for directory management, file operations, and path resolution that are already being used by the CLI.
    *   **Recommendation:** You SHOULD use these existing utilities throughout the codebase. The `get_project_root()`, `get_content_dir()`, `get_build_dir()` functions are essential for maintaining consistent path handling.

*   **File:** `requirements.txt`
    *   **Summary:** Contains all the required dependencies with proper version constraints matching the architecture specification.
    *   **Recommendation:** The dependencies are already correctly configured. Ensure this file stays synchronized with pyproject.toml dependencies.

### Implementation Tips & Notes

*   **Tip:** The project structure is already 90% complete. Most directories and placeholder files exist, including the complete package structure under `microblog/`, `templates/`, `static/`, `content/`, `tests/`, and `docs/` directories.

*   **Note:** The CLI entry point is already configured in pyproject.toml as `microblog = "microblog.cli:main"`, so the CLI will be installable once the package is installed with `pip install -e .`.

*   **Warning:** The task mentions creating a `.gitignore` file, but one already exists in the repository. You should READ the existing file first before making any changes to avoid overwriting important ignore rules.

*   **Tip:** The existing `README.md` is comprehensive and includes installation instructions, CLI usage, Docker setup, and project status. You should update the project status section to reflect task completion but preserve the existing content structure.

*   **Note:** Docker configuration files (`Dockerfile` and `docker-compose.yml`) already exist and appear to be properly configured for the project needs.

*   **Critical:** The task acceptance criteria mentions that "CLI tool installs successfully" and "`microblog --help` displays command structure". These requirements are already met by the existing code structure.

*   **Tip:** I found that the project uses a `Makefile` for development shortcuts. You should ensure any new commands or processes integrate with the existing Make targets.

*   **Important:** The CLI already imports from `microblog.utils` for path management. You MUST ensure all new code follows this pattern and doesn't hardcode paths.

*   **Note:** The directory structure in the codebase matches exactly with the specification from the planning documents. All required directories are already created with appropriate `__init__.py` files in Python packages.