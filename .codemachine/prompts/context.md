# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T5",
  "iteration_id": "I2",
  "iteration_goal": "Implement authentication system with JWT tokens, user management, and core data models for posts and images",
  "description": "Implement authentication middleware, CSRF protection, and session management for FastAPI application. Create login/logout endpoints with secure cookie handling.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Authentication flow from diagrams, security requirements, FastAPI middleware patterns",
  "target_files": ["microblog/server/middleware.py", "microblog/server/routes/auth.py"],
  "input_files": ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "docs/diagrams/auth_flow.puml"],
  "deliverables": "Authentication middleware, CSRF protection, login/logout endpoints, secure session management",
  "acceptance_criteria": "Middleware validates JWT tokens correctly, CSRF tokens prevent attacks, login sets httpOnly cookies, logout clears sessions properly",
  "dependencies": ["I2.T3"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: authentication-authorization (from 05_Operational_Architecture.md)

```markdown
**Authentication & Authorization:**

**Authentication Strategy:**
- **Single-User Design**: System supports exactly one admin user with fixed role
- **JWT-Based Sessions**: Stateless authentication using JSON Web Tokens
- **Secure Token Storage**: JWT stored in httpOnly, Secure, SameSite=Strict cookies
- **Password Security**: Bcrypt hashing with cost factor ≥12 for password storage
- **Session Management**: Configurable token expiration (default 2 hours)

**Implementation Details:**
```python
# Authentication flow
def authenticate_user(username: str, password: str) -> Optional[User]:
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        token = create_jwt_token(user.user_id, user.username)
        return user, token
    return None

# JWT Token Structure
{
    "user_id": 1,
    "username": "admin",
    "role": "admin",
    "exp": 1635724800,  # Expiration timestamp
    "iat": 1635721200   # Issued at timestamp
}
```

**Authorization Model:**
- **Role-Based**: Single admin role with full system access
- **Route Protection**: Middleware validates JWT for protected endpoints
- **CSRF Protection**: All state-changing operations require valid CSRF tokens
- **Session Validation**: Automatic token expiration and renewal handling
```

### Context: security-considerations (from 05_Operational_Architecture.md)

```markdown
**Security Considerations:**

**Input Validation & Sanitization:**
- **Markdown Sanitization**: HTML escaping by default to prevent XSS attacks
- **File Upload Validation**: Extension whitelist, MIME type verification, size limits
- **Path Traversal Prevention**: Filename sanitization and directory boundary enforcement
```

### Context: task-i2-t5 (from 02_Iteration_I2.md)

```markdown
*   **Task 2.5:**
    *   **Task ID:** `I2.T5`
    *   **Description:** Implement authentication middleware, CSRF protection, and session management for FastAPI application. Create login/logout endpoints with secure cookie handling.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Authentication flow from diagrams, security requirements, FastAPI middleware patterns
    *   **Input Files:** ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "docs/diagrams/auth_flow.puml"]
    *   **Target Files:** ["microblog/server/middleware.py", "microblog/server/routes/auth.py"]
    *   **Deliverables:** Authentication middleware, CSRF protection, login/logout endpoints, secure session management
    *   **Acceptance Criteria:** Middleware validates JWT tokens correctly, CSRF tokens prevent attacks, login sets httpOnly cookies, logout clears sessions properly
    *   **Dependencies:** `I2.T3`
    *   **Parallelizable:** No
```

### Context: core-architecture (from 01_Plan_Overview_and_Setup.md)

```markdown
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/auth/models.py`
    *   **Summary:** Complete User SQLite model with authentication methods, single-user constraint, and database operations.
    *   **Recommendation:** You MUST import and use the `User.get_by_username()` method for authentication. The model already handles bcrypt password verification and database queries.
*   **File:** `microblog/auth/jwt_handler.py`
    *   **Summary:** Complete JWT token creation and validation utilities with proper error handling and security features.
    *   **Recommendation:** You MUST import and use `create_jwt_token()` and `verify_jwt_token()` functions. These already integrate with the configuration system for JWT secrets.
*   **File:** `microblog/auth/password.py`
    *   **Summary:** Secure password hashing and verification utilities using bcrypt with cost factor ≥12.
    *   **Recommendation:** You SHOULD import and use `verify_password()` for credential verification during login.
*   **File:** `microblog/server/config.py`
    *   **Summary:** Configuration management system with Pydantic models for validation, including AuthConfig for JWT settings.
    *   **Recommendation:** You MUST import and use `get_config()` to access JWT secrets and session expiration settings. The AuthConfig class defines required JWT configuration.

### Implementation Tips & Notes
*   **Tip:** The authentication flow diagram at `docs/diagrams/auth_flow.puml` provides complete security implementation details including CSRF token handling and cookie security attributes. Follow this pattern exactly.
*   **Note:** The project uses FastAPI with Pydantic models. You should create appropriate request/response models for login endpoints following FastAPI conventions.
*   **Warning:** The JWT tokens must be stored in httpOnly cookies with Secure and SameSite=Strict attributes as specified in the security requirements. Do NOT use Authorization headers or localStorage.
*   **Tip:** The User model already implements single-user constraints and handles user existence checks. Use `User.user_exists()` to verify system setup.
*   **Note:** CSRF protection is required for all state-changing operations. Implement a proper CSRF token generation and validation system that integrates with forms.
*   **Warning:** The target files `microblog/server/middleware.py` and `microblog/server/routes/auth.py` do not exist yet - you need to create them from scratch.
*   **Tip:** The configuration system supports hot-reload and validation. Access auth settings through `config.auth.jwt_secret` and `config.auth.session_expires`.
*   **Note:** Follow the directory structure specified in the plan. The routes should be organized under `microblog/server/routes/` with proper module organization.