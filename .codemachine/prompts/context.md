# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T1",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Implement HTMX API endpoints for dynamic post operations including create, update, delete, and publish/unpublish with HTML fragment responses and proper error handling.",
  "agent_type_hint": "BackendAgent",
  "inputs": "HTMX integration patterns, API endpoint requirements, HTML fragment responses",
  "target_files": ["microblog/server/routes/api.py"],
  "input_files": ["microblog/server/routes/dashboard.py", "microblog/content/post_service.py"],
  "deliverables": "HTMX API endpoints, HTML fragment responses, dynamic post operations, error handling",
  "acceptance_criteria": "API endpoints return HTML fragments, HTMX requests work correctly, error responses are user-friendly, CSRF protection active",
  "dependencies": ["I4.T6"],
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

### Context: task-i5-t1 (from 02_Iteration_I5.md)

```markdown
    *   **Task 5.1:**
        *   **Task ID:** `I5.T1`
        *   **Description:** Implement HTMX API endpoints for dynamic post operations including create, update, delete, and publish/unpublish with HTML fragment responses and proper error handling.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** HTMX integration patterns, API endpoint requirements, HTML fragment responses
        *   **Input Files:** ["microblog/server/routes/dashboard.py", "microblog/content/post_service.py"]
        *   **Target Files:** ["microblog/server/routes/api.py"]
        *   **Deliverables:** HTMX API endpoints, HTML fragment responses, dynamic post operations, error handling
        *   **Acceptance Criteria:** API endpoints return HTML fragments, HTMX requests work correctly, error responses are user-friendly, CSRF protection active
        *   **Dependencies:** `I4.T6`
        *   **Parallelizable:** Yes
```

### Context: htmx-integration (from 04_Behavior_and_Communication.md)

```markdown
**Communication Patterns:**

1. **Synchronous Request/Response**: Standard HTTP interactions for page loads and API calls
2. **HTMX Partial Updates**: Dynamic content updates without full page refreshes
3. **Server-Sent Events**: Real-time build progress updates (future enhancement)
4. **File System Events**: Configuration hot-reload through file watchers (development mode)

**Detailed API Endpoints:**

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
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/routes/dashboard.py`
    *   **Summary:** This file contains existing dashboard routes for serving HTML pages and currently has preliminary API endpoints (`/dashboard/api/posts` and `/dashboard/api/posts/{slug}`) that handle form-based POST requests and return redirects. These routes provide the foundation for understanding how post operations work but need to be adapted for HTMX HTML fragment responses.
    *   **Recommendation:** You MUST study the existing API endpoints in lines 254-376 to understand the post creation and update logic. You SHOULD extract the core business logic patterns and adapt them for the new `/api/posts` endpoints that return HTML fragments instead of redirects.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file contains the complete PostService class with all CRUD operations for posts including create, update, delete, publish/unpublish operations. It handles markdown file processing, YAML frontmatter, validation, and error handling.
    *   **Recommendation:** You MUST import and use the `get_post_service()` function from this file. The service provides methods like `create_post()`, `update_post()`, `delete_post()`, `publish_post()`, and `unpublish_post()` that you SHOULD use directly in your API endpoints.

*   **File:** `microblog/server/middleware.py`
    *   **Summary:** This file contains authentication and CSRF protection middleware with helper functions for getting current user and validating CSRF tokens. It provides `get_current_user()`, `require_authentication()`, `get_csrf_token()`, and `validate_csrf_from_form()` functions.
    *   **Recommendation:** You MUST use `require_authentication(request)` to ensure authenticated access and `validate_csrf_from_form(request, form_data)` for CSRF validation in state-changing operations. The CSRF protection middleware expects tokens in headers as 'X-CSRF-Token'.

*   **File:** `templates/dashboard/posts_list.html`
    *   **Summary:** This template already contains JavaScript code that expects HTMX endpoints like `/api/posts/{slug}/publish`, `/api/posts/{slug}/unpublish`, and `DELETE /api/posts/{slug}`. The template shows how HTML fragments should be structured for post operations.
    *   **Recommendation:** You MUST ensure your API endpoints return HTML fragments that are compatible with the existing HTMX code in lines 452-492. The template expects these endpoints to work with HTMX and reload the page after operations.

### Implementation Tips & Notes

*   **Tip:** The existing dashboard API endpoints in `dashboard.py` (lines 254-376) show the exact form field structure and validation logic needed. You SHOULD reuse this logic but modify the response format from redirects to HTML fragments.

*   **Note:** The posts_list.html template already contains HTMX JavaScript calls (lines 452-492) that expect specific API endpoints to exist. You MUST implement exactly these endpoints: `DELETE /api/posts/{slug}`, `POST /api/posts/{slug}/publish`, and `POST /api/posts/{slug}/unpublish`.

*   **Warning:** The middleware expects CSRF tokens in the 'X-CSRF-Token' header for API calls. The existing templates set this header using `document.querySelector('meta[name="csrf-token"]').getAttribute('content')`. You MUST ensure your endpoints validate this properly.

*   **Tip:** The target file `microblog/server/routes/api.py` does not exist yet. You need to create it and ensure it's imported and registered in the FastAPI application. Look at how `dashboard.py` and `auth.py` are structured for the pattern to follow.

*   **Note:** The post service uses specific exception types (`PostNotFoundError`, `PostValidationError`, `PostFileError`) that you SHOULD catch and convert to appropriate HTTP status codes and HTML error fragments for HTMX consumption.

*   **Warning:** The existing form handling in dashboard.py processes forms with specific field names like `title`, `content`, `new_slug`, `tags`, `post_date`, `draft`. Your API endpoints MUST handle the same field structure to maintain consistency.