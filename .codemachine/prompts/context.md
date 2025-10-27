# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T6",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Implement post editing interface with markdown textarea, metadata fields, and form validation. Create post creation and editing templates with proper form handling.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Post editing requirements, form validation, markdown editing interface",
  "target_files": ["templates/dashboard/post_edit.html", "microblog/server/routes/dashboard.py"],
  "input_files": ["microblog/content/post_service.py", "templates/dashboard/layout.html"],
  "deliverables": "Post editing interface, form validation, metadata management, create/edit templates",
  "acceptance_criteria": "Post creation form works, editing loads existing posts, validation prevents invalid data, draft/publish status manageable",
  "dependencies": ["I4.T5"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: task-i4-t6 (from 02_Iteration_I4.md)

```markdown
<!-- anchor: task-i4-t6 -->
*   **Task 4.6:**
    *   **Task ID:** `I4.T6`
    *   **Description:** Implement post editing interface with markdown textarea, metadata fields, and form validation. Create post creation and editing templates with proper form handling.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Post editing requirements, form validation, markdown editing interface
    *   **Input Files:** ["microblog/content/post_service.py", "templates/dashboard/layout.html"]
    *   **Target Files:** ["templates/dashboard/post_edit.html", "microblog/server/routes/dashboard.py"]
    *   **Deliverables:** Post editing interface, form validation, metadata management, create/edit templates
    *   **Acceptance Criteria:** Post creation form works, editing loads existing posts, validation prevents invalid data, draft/publish status manageable
    *   **Dependencies:** `I4.T5`
    *   **Parallelizable:** Yes
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** Comprehensive post service with CRUD operations for markdown posts with YAML frontmatter. Provides create_post(), update_post(), get_post_by_slug(), and validation methods.
    *   **Recommendation:** You MUST import and use the `get_post_service()` function from this file for all post operations. The service already handles file operations, validation, and slug generation.

*   **File:** `microblog/server/routes/dashboard.py`
    *   **Summary:** Dashboard routes including authentication, CSRF token handling, and existing API endpoints for post creation/updates. Contains `/dashboard/posts/new` and `/dashboard/posts/{slug}/edit` routes that serve the post_edit.html template.
    *   **Recommendation:** The routes already exist and are functional. You need to ensure the form submissions work correctly with the existing `create_post_api()` and `update_post_api()` endpoints. Pay attention to the form field names and data parsing logic.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** Complete dashboard layout with Pico.css styling, navigation, CSRF token configuration, and HTMX setup. Includes CSRF token meta tag and HTMX request configuration.
    *   **Recommendation:** The layout is fully functional. You MUST use the established patterns for CSRF tokens and ensure your forms follow the existing styling conventions.

*   **File:** `templates/dashboard/post_edit.html`
    *   **Summary:** Complete post editing template with form fields for all metadata (title, slug, description, tags, date, draft status) and content textarea. Includes JavaScript for slug auto-generation and form handling.
    *   **Recommendation:** The template is nearly complete but needs some fixes. The form action URLs and method handling need adjustment to work with the existing API endpoints.

*   **File:** `microblog/content/validators.py`
    *   **Summary:** Post validation models using dataclasses - PostFrontmatter and PostContent classes with built-in validation logic.
    *   **Recommendation:** The validation is already integrated into the post service. The existing validation rules include title length limits (200 chars), slug limits (200 chars), and description limits (300 chars).

### Implementation Tips & Notes

*   **Tip:** The post editing template already exists and is mostly functional. The main issue is that the form action URLs and JavaScript fetch logic are not aligned with the existing API endpoints.

*   **Note:** The dashboard routes already provide endpoints at `/dashboard/posts/new` and `/dashboard/posts/{slug}/edit` that render the post_edit.html template. The API endpoints `/dashboard/api/posts` (POST) and `/dashboard/api/posts/{slug}` (POST, not PUT) handle form submissions.

*   **Warning:** The existing `update_post_api()` function expects a POST request to `/dashboard/api/posts/{slug}`, not a PUT request. The current template tries to use a PUT method via a hidden `_method` field, but FastAPI doesn't automatically handle method override. You need to ensure the form submits as POST.

*   **Critical:** The form field names in the template MUST match exactly what the API endpoints expect. The existing API expects: `title`, `content`, `new_slug` (not `slug` for updates), `description`, `tags`, `date`, `draft`.

*   **Security:** CSRF protection is already implemented. The layout template includes the CSRF token in a meta tag, and the JavaScript is configured to include it in HTMX requests.

*   **Validation:** Client-side validation exists for slug auto-generation and form state checking. Server-side validation is handled by the post service and will return appropriate errors.

*   **Form Handling:** The existing JavaScript in post_edit.html uses fetch() API for form submission, but the endpoints expect standard form submission. The form action should point to the correct dashboard API endpoints (`/dashboard/api/posts` or `/dashboard/api/posts/{slug}`), not `/api/posts`.