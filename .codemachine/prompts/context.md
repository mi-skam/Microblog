# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T2",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Implement FastAPI application setup with middleware configuration, route registration, and CORS/security headers. Create application factory pattern for testing and deployment.",
  "agent_type_hint": "BackendAgent",
  "inputs": "FastAPI best practices, middleware requirements, security headers specification",
  "target_files": ["microblog/server/app.py"],
  "input_files": ["microblog/server/middleware.py", "microblog/server/config.py"],
  "deliverables": "FastAPI application setup, middleware integration, security configuration, application factory",
  "acceptance_criteria": "Application starts successfully, middleware functions correctly, security headers set, CORS configured properly",
  "dependencies": ["I2.T5"],
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

**Key Technology Decisions:**

**Python Ecosystem Choice:**
- Extensive text processing libraries ideal for markdown and template rendering
- Mature web framework options with strong security foundations
- Excellent CLI development tools and filesystem management capabilities
- Strong type system support for maintainable code

**FastAPI Selection:**
- Async support for handling concurrent dashboard operations
- Automatic request/response validation with Pydantic models
- Built-in security middleware for CSRF, CORS, and authentication
- Excellent documentation generation and development experience

**Static Generation Strategy:**
- Jinja2 templates provide flexibility for custom themes and layouts
- python-markdown offers extensive plugin ecosystem for future enhancements
- Separation of content (markdown) from presentation (templates) enables design iteration

**HTMX for Interactivity:**
- Maintains server-side rendering benefits while adding dynamic behavior
```

### Context: security-considerations (from 05_Operational_Architecture.md)

```markdown
**Security Headers Configuration:**
```python
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'"
}
```

**Data Protection:**
- **Secrets Management**: JWT secret stored in configuration with minimum 32-character requirement
- **Database Security**: SQLite file permissions restricted to application user
- **File System Security**: Content directory permissions preventing unauthorized access
- **Backup Security**: Build backups stored with same security constraints as primary data

**Vulnerability Mitigation:**
- **Rate Limiting**: Authentication endpoint protection against brute force attacks
- **CSRF Protection**: Synchronizer token pattern for all state-changing operations
- **Session Security**: Automatic token expiration and secure cookie attributes
- **Dependency Scanning**: Regular security updates for Python dependencies
```

### Context: task-i4-t2 (from 02_Iteration_I4.md)

```markdown
    <!-- anchor: task-i4-t2 -->
    *   **Task 4.2:**
        *   **Task ID:** `I4.T2`
        *   **Description:** Implement FastAPI application setup with middleware configuration, route registration, and CORS/security headers. Create application factory pattern for testing and deployment.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** FastAPI best practices, middleware requirements, security headers specification
        *   **Input Files:** ["microblog/server/middleware.py", "microblog/server/config.py"]
        *   **Target Files:** ["microblog/server/app.py"]
        *   **Deliverables:** FastAPI application setup, middleware integration, security configuration, application factory
        *   **Acceptance Criteria:** Application starts successfully, middleware functions correctly, security headers set, CORS configured properly
        *   **Dependencies:** `I2.T5`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/server/middleware.py`
    *   **Summary:** This file contains three complete middleware classes: `AuthenticationMiddleware` for JWT authentication, `CSRFProtectionMiddleware` for CSRF protection, and `SecurityHeadersMiddleware` for security headers. It also provides utility functions for current user access and CSRF validation.
    *   **Recommendation:** You MUST import and use these middleware classes directly in your FastAPI app setup. The middleware is already fully implemented and includes all security features specified in the architecture.
*   **File:** `microblog/server/config.py`
    *   **Summary:** This file provides a complete configuration management system with `ConfigManager` class and `AppConfig` models including `SiteConfig`, `BuildConfig`, `ServerConfig`, and `AuthConfig`. It includes validation, hot-reload support, and global access functions.
    *   **Recommendation:** You MUST use `get_config()` function to access configuration throughout your app. The configuration includes all necessary server settings including host, port, and hot_reload options.
*   **File:** `microblog/server/routes/auth.py`
    *   **Summary:** This file defines a complete authentication router with login/logout endpoints, both HTML and API versions, and session checking capabilities. It uses FastAPI's `APIRouter` pattern.
    *   **Recommendation:** You MUST follow the same router pattern for organizing routes. Import this router and include it in your main app using `app.include_router(auth.router)`.
*   **File:** `pyproject.toml`
    *   **Summary:** This file shows all required dependencies are already specified, including FastAPI 0.100+, uvicorn, and all security/middleware dependencies.
    *   **Recommendation:** All necessary packages are available. You can import FastAPI, CORS middleware, and other required components directly.

### Implementation Tips & Notes
*   **Tip:** The middleware classes are already fully implemented with proper error handling and security features. You should instantiate them in the order: `SecurityHeadersMiddleware`, `CSRFProtectionMiddleware`, `AuthenticationMiddleware` for proper layering.
*   **Note:** The `ConfigManager` supports both development and production modes via the `dev_mode` parameter. You SHOULD use this to enable hot-reload only in development.
*   **Warning:** The middleware expects specific protected paths like `/dashboard`, `/api/`, `/admin/`. Ensure your route structure aligns with these protection patterns.
*   **Tip:** The existing auth router shows how to integrate templates properly. You'll need to set up Jinja2Templates for any additional routes that serve HTML.
*   **Note:** The configuration system is designed to be used globally through `get_config()`. You SHOULD use this function rather than creating new ConfigManager instances.
*   **Important:** The `SecurityHeadersMiddleware` already implements all required security headers from the architecture specification. You do NOT need to add additional security header configuration.
*   **Pattern:** Use the application factory pattern by creating a function like `create_app()` that returns a configured FastAPI instance. This supports both development and production deployment scenarios.