# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T6",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Enhance dashboard templates with HTMX attributes, interactive elements, and dynamic content updates. Add confirmation dialogs, inline editing, and responsive feedback.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "HTMX enhancement patterns, user interaction requirements, responsive design",
  "target_files": ["templates/dashboard/posts_list.html", "templates/dashboard/post_edit.html", "static/js/dashboard.js"],
  "input_files": ["templates/dashboard/posts_list.html", "templates/dashboard/post_edit.html", "static/js/htmx.min.js"],
  "deliverables": "HTMX-enhanced templates, interactive elements, dynamic updates, confirmation dialogs, responsive feedback",
  "acceptance_criteria": "HTMX interactions work smoothly, confirmations prevent accidental deletions, inline editing functional, feedback is immediate and clear",
  "dependencies": ["I5.T3", "I5.T5"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

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

### Context: communication-patterns (from 04_Behavior_and_Communication.md)

```markdown
**Communication Patterns:**

1. **Synchronous Request/Response**: Standard HTTP interactions for page loads and API calls
2. **HTMX Partial Updates**: Dynamic content updates without full page refreshes
3. **Server-Sent Events**: Real-time build progress updates (future enhancement)
4. **File System Events**: Configuration hot-reload through file watchers (development mode)
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

### Context: task-i5-t6 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.6:**
    *   **Task ID:** `I5.T6`
    *   **Description:** Enhance dashboard templates with HTMX attributes, interactive elements, and dynamic content updates. Add confirmation dialogs, inline editing, and responsive feedback.
    *   **Agent Type Hint:** `FrontendAgent`
    *   **Inputs:** HTMX enhancement patterns, user interaction requirements, responsive design
    *   **Input Files:** ["templates/dashboard/posts_list.html", "templates/dashboard/post_edit.html", "static/js/htmx.min.js"]
    *   **Target Files:** ["templates/dashboard/posts_list.html", "templates/dashboard/post_edit.html", "static/js/dashboard.js"]
    *   **Deliverables:** HTMX-enhanced templates, interactive elements, dynamic updates, confirmation dialogs, responsive feedback
    *   **Acceptance Criteria:** HTMX interactions work smoothly, confirmations prevent accidental deletions, inline editing functional, feedback is immediate and clear
    *   **Dependencies:** `I5.T3`, `I5.T5`
    *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `templates/dashboard/posts_list.html`
    *   **Summary:** This file contains the posts listing interface with traditional JavaScript onclick handlers. It has a complete posts table, action buttons (Edit, Publish/Unpublish, Delete), and a modal dialog for delete confirmation.
    *   **Recommendation:** You MUST replace the existing JavaScript onclick handlers (publishPost, unpublishPost, deletePost) with HTMX attributes for seamless interactions. The file currently reloads the entire page after operations - this should be changed to dynamic HTML fragment updates.

*   **File:** `templates/dashboard/post_edit.html`
    *   **Summary:** This file contains the post editing interface with a live markdown preview already implemented using HTMX. It has proper form submission handling and preview functionality.
    *   **Recommendation:** The preview functionality is already well-implemented with HTMX. You SHOULD enhance the form submission to use HTMX instead of the current fetch-based approach, and add inline validation feedback.

*   **File:** `static/js/dashboard.js`
    *   **Summary:** This file contains comprehensive dashboard enhancements including preview functionality, auto-save, scroll synchronization, and keyboard shortcuts. It's well-structured with modular functions.
    *   **Recommendation:** You SHOULD extend this file to work seamlessly with HTMX. The auto-save and unsaved changes warnings should be maintained, but adapted for HTMX-based form submissions.

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file contains all the HTMX API endpoints that return HTML fragments. It includes endpoints for post CRUD operations (/api/posts), preview (/api/preview), image upload, and build management.
    *   **Recommendation:** You MUST use these existing API endpoints in your HTMX implementations. All endpoints are already designed to return HTML fragments with proper error handling.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** This file contains the base layout with HTMX already loaded from CDN (htmx.org@1.9.10) and CSRF token configuration. It has proper HTMX setup for all requests.
    *   **Recommendation:** The HTMX infrastructure is already properly set up. You SHOULD use the existing CSRF token configuration and ensure all your HTMX requests include the proper headers.

### Implementation Tips & Notes

*   **Tip:** HTMX is already loaded and configured in the layout template with automatic CSRF token inclusion. You don't need to handle CSRF tokens manually - they're automatically added to all HTMX requests.
*   **Note:** The current post list uses window.location.reload() after HTMX operations. You SHOULD replace this with targeted HTML fragment updates using hx-target and hx-swap to make interactions more seamless.
*   **Warning:** The existing JavaScript in posts_list.html uses htmx.ajax() for operations but still reloads the page. This defeats the purpose of HTMX. You should convert these to proper HTMX attributes on buttons.
*   **Tip:** The API endpoints in /api/ already return properly formatted HTML fragments with success/error messages. Use hx-swap-oob="true" for out-of-band updates to display messages.
*   **Note:** The post edit form currently uses a complex fetch-based submission. You SHOULD replace this with HTMX form submission (hx-post/hx-put) for consistency.
*   **Tip:** For confirmation dialogs, you can use hx-confirm attribute which provides built-in confirmation functionality, or enhance the existing modal system to work with HTMX.
*   **Warning:** Be careful to maintain the existing auto-save functionality in dashboard.js when implementing HTMX form submissions. The auto-save should continue working independently.
*   **Tip:** Use hx-indicator for loading states on buttons and forms to provide visual feedback during operations.
*   **Note:** The preview functionality in post_edit.html is already well-implemented with HTMX debouncing (delay:500ms). This is a good reference for implementing other HTMX interactions.