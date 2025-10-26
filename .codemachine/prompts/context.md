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
*   **File:** `.gitignore`
    *   **Summary:** Contains basic ignore rules for .codemachine directories and node_modules.
    *   **Recommendation:** You MUST expand this file to include Python-specific ignores (build/, *.pyc, __pycache__, .env, etc.) and the project-specific ignore patterns mentioned in the directory structure (build/, build.bak/).

### Implementation Tips & Notes
*   **Critical:** The project directory is currently empty except for .codemachine artifacts and .gitignore. This is task I1.T1 - the foundation setup task.
*   **Tip:** You MUST create the complete directory structure as specified in the plan document. Every directory and subdirectory listed should be created.
*   **Note:** The pyproject.toml should use modern Python packaging standards and include all dependencies listed in the technology stack table.
*   **Warning:** Pay careful attention to the exact dependencies and versions specified in the technology stack. Use Click for CLI, FastAPI 0.100+, python-markdown, pymdown-extensions, python-jose, passlib[bcrypt], Jinja2, watchfiles, uvicorn, and ruff.
*   **Tip:** The CLI entry point should be configured in pyproject.toml to expose the `microblog` command.
*   **Note:** Create placeholder files with appropriate docstrings for all modules to establish the architecture, but don't implement full functionality yet - that's for later tasks.
*   **Important:** The acceptance criteria states that `microblog --help` must work, so ensure the CLI framework is properly set up with basic commands for build and serve operations.
*   **Docker:** Include Dockerfile and docker-compose.yml for development environment as specified in target_files.
*   **Documentation:** Create a comprehensive README.md that explains the project setup and basic usage.