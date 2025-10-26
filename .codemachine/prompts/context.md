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

**Communication Patterns:**

1. **Synchronous Request/Response**: Standard HTTP interactions for page loads and API calls
2. **HTMX Partial Updates**: Dynamic content updates without full page refreshes
3. **Server-Sent Events**: Real-time build progress updates (future enhancement)
4. **File System Events**: Configuration hot-reload through file watchers (development mode)
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

### Context: htmx-integration (from 04_Behavior_and_Communication.md)

```markdown
**HTMX Integration Patterns:**

1. **Live Form Validation**
```html
<input name="title"
       hx-post="/api/validate/title"
       hx-trigger="blur"
       hx-target="#title-feedback">
```

2. **Dynamic Content Updates**
```html
<button hx-delete="/api/posts/123"
        hx-confirm="Delete this post?"
        hx-target="#post-123"
        hx-swap="outerHTML">Delete</button>
```

3. **Live Markdown Preview**
```html
<textarea name="content"
          hx-post="/api/preview"
          hx-trigger="keyup changed delay:500ms"
          hx-target="#preview-pane">
```

4. **Build Progress Updates**
```html
<button hx-post="/api/build"
        hx-target="#build-status"
        hx-indicator="#build-spinner">Rebuild Site</button>
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
      "field": ["Field-specific error message"]
    }
  }
}
```
```

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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `docs/api/openapi.yaml`
    *   **Summary:** This file contains a complete, comprehensive OpenAPI v3 specification that matches all the requirements described in the task. It includes authentication endpoints, dashboard routes, HTMX API endpoints, detailed schemas, security definitions, and error handling patterns.
    *   **Recommendation:** **CRITICAL**: The OpenAPI specification already exists and appears to be complete! You should READ this file thoroughly and validate it against the task requirements rather than creating a new one from scratch.

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains a sophisticated configuration management system with Pydantic models for SiteConfig, BuildConfig, ServerConfig, and AuthConfig. It includes hot-reload support, validation, and YAML parsing.
    *   **Recommendation:** You SHOULD reference the Pydantic models in this file (SiteConfig, BuildConfig, ServerConfig, AuthConfig, AppConfig) when validating that the OpenAPI schemas match the actual configuration structure used in the codebase.

*   **File:** `content/_data/config.yaml`
    *   **Summary:** This file contains the actual configuration data structure with site settings, build settings, server settings, and authentication configuration.
    *   **Recommendation:** You SHOULD verify that the OpenAPI configuration schemas match the structure and values shown in this real configuration file.

*   **File:** `microblog/cli.py`
    *   **Summary:** This file contains the CLI interface with basic command structure for build, serve, create-user, init, and status commands. Most functionality is marked as "TODO: Implement in future iterations."
    *   **Recommendation:** While not directly related to the OpenAPI spec, this shows that the project is designed to have both CLI and web API interfaces, which supports the dual-interface approach described in the OpenAPI spec.

### Implementation Tips & Notes

*   **Tip:** The task appears to be essentially complete! The existing `docs/api/openapi.yaml` file contains a comprehensive OpenAPI v3 specification with 1,136 lines covering all required endpoints, schemas, security definitions, and documentation. You should validate this against the requirements rather than rewrite it.

*   **Note:** The OpenAPI specification includes sophisticated features like:
     - Complete authentication flows with JWT cookies and CSRF protection
     - Dual response formats (HTML fragments for HTMX, JSON for API consumption)
     - Comprehensive error handling with standardized error response formats
     - Detailed schemas for all configuration models that match the Pydantic models in `config.py`
     - Proper security scheme definitions for JWT cookies and CSRF tokens

*   **Warning:** The task deliverable asks for "Complete OpenAPI v3 YAML specification file" but this already exists. You should verify if this is actually a completion/validation task rather than a creation task.

*   **Validation Strategy:** You should:
     1. Validate the OpenAPI spec syntax using an OpenAPI validator
     2. Cross-reference the schemas with the actual Pydantic models in `config.py`
     3. Ensure all endpoints mentioned in the architecture documentation are included
     4. Verify that authentication flows match the specifications in the architecture docs
     5. Check that error response formats align with the documented error handling strategy

*   **Key Insight:** The existing OpenAPI specification shows evidence of being carefully crafted to match the "HTML-first" design pattern with HTMX enhancement that is central to this project's architecture. This suggests the spec is not just complete but also architecturally sound.