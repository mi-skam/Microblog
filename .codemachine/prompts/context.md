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

### Context: api-endpoints-detail (from 04_Behavior_and_Communication.md)

```markdown
**Detailed API Endpoints:**

**Dashboard API Endpoints:**
```
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file already contains a complete HTMX API implementation with all required endpoints (POST /api/posts, PUT /api/posts/{slug}, DELETE /api/posts/{slug}, POST /api/posts/{slug}/publish, POST /api/posts/{slug}/unpublish).
    *   **Recommendation:** The task appears to be already completed! The file contains all required HTMX endpoints with HTML fragment responses, proper error handling, and CSRF protection.

*   **File:** `microblog/server/routes/dashboard.py`
    *   **Summary:** Contains traditional dashboard routes with server-side rendering and basic API endpoints that redirect. Uses proper authentication and CSRF protection through middleware.
    *   **Recommendation:** You can reference this file for consistent form parsing patterns and error handling approaches, but the HTMX-specific implementation should be in api.py.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** Provides comprehensive post CRUD operations including create_post(), update_post(), delete_post(), publish_post(), and unpublish_post() methods with proper validation and error handling.
    *   **Recommendation:** The API endpoints already correctly use these service methods. All required post operations are available and properly integrated.

*   **File:** `microblog/server/middleware.py`
    *   **Summary:** Implements JWT authentication middleware and CSRF protection. Provides helper functions like require_authentication() and get_csrf_token() for route handlers.
    *   **Recommendation:** The API routes already use require_authentication() correctly. CSRF validation is handled automatically by middleware for /api/ paths.

*   **File:** `microblog/server/app.py`
    *   **Summary:** FastAPI application factory with proper middleware configuration including authentication, CSRF protection, and security headers. Routes are registered correctly.
    *   **Recommendation:** The API router is already registered properly in the application. No changes needed here.

### Implementation Tips & Notes

*   **Critical Finding:** The task appears to be already implemented! The `microblog/server/routes/api.py` file contains:
    - All required HTMX API endpoints (POST, PUT, DELETE, publish/unpublish)
    - HTML fragment responses using _create_error_fragment() and _create_success_fragment() helper functions
    - Proper error handling with appropriate HTTP status codes (201, 422, 404, 500)
    - Authentication via require_authentication() middleware helper
    - CSRF protection automatically handled by middleware for /api/ routes
    - Integration with post_service for all CRUD operations

*   **Tip:** The existing implementation follows the architectural patterns exactly as specified:
    - Uses `hx-swap-oob="true"` for out-of-band updates
    - Returns appropriate HTTP status codes (201 for creation, 200 for updates, etc.)
    - Includes JavaScript redirects for post-operation navigation
    - Handles all PostService exceptions properly (PostValidationError, PostNotFoundError, PostFileError)

*   **Warning:** Before proceeding with any changes, verify that the current implementation meets the acceptance criteria:
    - ✅ API endpoints return HTML fragments
    - ✅ HTMX requests work correctly (implementation looks correct)
    - ✅ Error responses are user-friendly (uses alert styling)
    - ✅ CSRF protection active (middleware handles this automatically)

*   **Recommendation:** Review the current implementation against the acceptance criteria. If it meets all requirements, the task should be marked as completed rather than reimplemented. The code quality is high and follows all specified patterns.