# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T1",
  "iteration_id": "I2",
  "iteration_goal": "Implement authentication system with JWT tokens, user management, and core data models for posts and images",
  "description": "Create OpenAPI v3 specification defining all authentication, dashboard, and HTMX API endpoints. Include request/response schemas, authentication requirements, and error response formats.",
  "agent_type_hint": "DocumentationAgent",
  "inputs": "API contract style from Section 2, endpoint requirements from specification, authentication flow patterns",
  "target_files": ["docs/api/openapi.yaml"],
  "input_files": [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md", "microblog/server/config.py"],
  "deliverables": "Complete OpenAPI v3 YAML specification file",
  "acceptance_criteria": "OpenAPI spec validates against schema, includes all required endpoints, request/response models are complete, authentication flows documented",
  "dependencies": ["I1.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: api-design-communication (from 04_Behavior_and_Communication.md)

```markdown
### 3.7. API Design & Communication

**API Style:** RESTful HTTP API with HTMX Enhancement

The MicroBlog system employs a RESTful API design enhanced with HTMX for dynamic interactions. This approach provides a traditional web application experience while enabling progressive enhancement through AJAX-style interactions without complex JavaScript frameworks.

**API Design Principles:**
- **REST-compliant**: Standard HTTP methods (GET, POST, PUT, DELETE) with semantic URLs
- **HTML-first**: Primary responses are HTML fragments for HTMX consumption
- **Progressive Enhancement**: All functionality works with and without JavaScript
- **Stateless**: JWT-based authentication eliminates server-side session management
- **CSRF Protection**: All state-changing operations include CSRF token validation

**API Categories:**

1. **Authentication Endpoints**
   - `POST /auth/login` - User authentication with credential validation
   - `POST /auth/logout` - Session termination and cookie clearing
   - `GET /auth/check` - Session validation for protected routes

2. **Dashboard Page Routes**
   - `GET /dashboard` - Main dashboard with post listing
   - `GET /dashboard/posts/new` - New post creation form
   - `GET /dashboard/posts/{id}/edit` - Post editing interface
   - `GET /dashboard/settings` - Configuration management interface

3. **HTMX API Endpoints**
   - `POST /api/posts` - Create new post with live feedback
   - `PUT /api/posts/{id}` - Update existing post content
   - `DELETE /api/posts/{id}` - Delete post with confirmation
   - `POST /api/posts/{id}/publish` - Toggle post publication status
   - `POST /api/build` - Trigger site rebuild with progress updates
   - `POST /api/images` - Handle image uploads with validation
```

### Context: api-endpoints-detail (from 04_Behavior_and_Communication.md)

```markdown
**Detailed API Endpoints:**

**Authentication Endpoints:**
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin&password=secret&csrf_token=...
Response: 302 Redirect + Set-Cookie: jwt=...; HttpOnly; Secure; SameSite=Strict

POST /auth/logout
Response: 302 Redirect + Set-Cookie: jwt=; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

**Dashboard API Endpoints:**
```
GET /dashboard
Headers: Cookie: jwt=...
Response: 200 OK + HTML dashboard page

POST /api/posts
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Content-Type: application/json
Body: {
  "title": "My New Post",
  "content": "# Hello World\nThis is my post content",
  "tags": ["tech", "blogging"],
  "draft": true
}
Response: 201 Created + HTML fragment with post data

PUT /api/posts/123
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Content-Type: application/json
Body: { "title": "Updated Title", "content": "...", "draft": false }
Response: 200 OK + HTML fragment with updated post

DELETE /api/posts/123
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Response: 200 OK + HTML fragment removing post from list

POST /api/build
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Response: 202 Accepted + HTML fragment with build progress
```

**Image Upload Endpoint:**
```
POST /api/images
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Content-Type: multipart/form-data
Body: file=@image.jpg
Response: 201 Created + JSON with image URL and markdown snippet
{
  "filename": "2025-10-26-image.jpg",
  "url": "../images/2025-10-26-image.jpg",
  "markdown": "![Image description](../images/2025-10-26-image.jpg)"
}
```
```

### Context: error-handling-api (from 04_Behavior_and_Communication.md)

```markdown
**API Error Handling:**

**Standard HTTP Status Codes:**
- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data or validation errors
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: CSRF token invalid or insufficient permissions
- `404 Not Found`: Requested resource does not exist
- `422 Unprocessable Entity`: Validation errors with detailed field information
- `500 Internal Server Error`: Unexpected server error

**Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid post data provided",
    "details": {
      "title": ["Title is required and must be between 1-200 characters"],
      "content": ["Content cannot be empty"]
    }
  }
}
```

**HTMX Error Handling:**
```html
<!-- Error responses return HTML fragments for display -->
<div class="error-message" hx-swap-oob="true" id="error-container">
  <p>Failed to save post. Please check your inputs and try again.</p>
</div>
```
```

### Context: key-architectural-artifacts (from 01_Plan_Overview_and_Setup.md)

```markdown
## 2.1. Key Architectural Artifacts Planned

*   **Component Diagram (PlantUML)** - To visualize dashboard application internal structure and service interactions *(Created in I1.T2)*
*   **Database ERD (PlantUML)** - To show entity relationships between User, Posts, Images, and Configuration *(Created in I1.T3)*
*   **API Specification (OpenAPI v3 YAML)** - To define authentication, dashboard, and HTMX API endpoints *(Created in I2.T1)*
*   **Authentication Flow Diagram (PlantUML)** - To illustrate JWT-based login and session management process *(Created in I2.T2)*
*   **Build Process Sequence Diagram (PlantUML)** - To show atomic build workflow with backup and rollback *(Created in I3.T1)*
*   **Deployment Architecture Diagram (PlantUML)** - To visualize production deployment options and configurations *(Created in I5.T2)*
*   **Directory Structure Documentation (Markdown)** - To define project organization and file placement standards *(Created in I1.T1)*
*   **Configuration Schema (JSON Schema)** - To validate YAML configuration files and document settings *(Created in I4.T1)*
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains the complete configuration management system with Pydantic models for SiteConfig, BuildConfig, ServerConfig, and AuthConfig. It includes validation, hot-reload capabilities, and JSON schema generation.
    *   **Recommendation:** You MUST reference these exact configuration models when defining API request/response schemas. The AuthConfig model shows JWT token and session configuration that will be used in authentication endpoints.
*   **File:** `content/_data/config.yaml`
    *   **Summary:** This is the actual configuration file with default values for site, build, server, and auth settings.
    *   **Recommendation:** Use this file to understand the actual data structures and default values that will be used in the API endpoints.
*   **File:** `docs/config_schema.json`
    *   **Summary:** This file contains the complete JSON Schema for configuration validation, generated from the Pydantic models.
    *   **Recommendation:** You SHOULD reference this schema structure when defining configuration-related API endpoints in the OpenAPI spec.
*   **File:** `pyproject.toml`
    *   **Summary:** This file shows the complete technology stack including FastAPI 0.100+, python-jose for JWT, passlib[bcrypt] for password hashing, and python-multipart for file uploads.
    *   **Recommendation:** You MUST ensure the OpenAPI spec is compatible with FastAPI 0.100+ and includes proper security schemes for JWT authentication.

### Implementation Tips & Notes
*   **Tip:** The project follows a clear directory structure where API documentation goes in `docs/api/`. The target file `docs/api/openapi.yaml` should be created in this exact location.
*   **Note:** The configuration system already includes comprehensive Pydantic models with validation. When defining request/response schemas, you should align with the existing Pydantic field types and validation rules.
*   **Important:** The API is designed as "HTML-first" with HTMX enhancement. This means most API endpoints should define both JSON and HTML fragment response types, with HTML being the primary response for HTMX requests.
*   **Security Note:** The system uses JWT tokens in httpOnly cookies with CSRF protection. The OpenAPI spec MUST include proper security definitions for both cookie-based authentication and CSRF token validation.
*   **Warning:** The project uses single-user authentication design. Do not define multi-user or role-based access control in the API specification.
*   **Convention:** Error responses follow a standardized format with "error" wrapper object containing "code", "message", and optional "details" fields. This MUST be consistently defined across all endpoints.
*   **File Upload:** The system supports multipart/form-data for image uploads with specific response format including filename, URL, and markdown snippet generation. This exact response format is specified in the architecture documentation.