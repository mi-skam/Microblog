# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T3",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Implement live markdown preview functionality with HTMX, debounced input handling, and real-time HTML rendering. Create preview pane in post editing interface.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Live preview requirements, HTMX patterns, debouncing strategy, markdown rendering",
  "target_files": ["microblog/server/routes/api.py", "templates/dashboard/post_edit.html", "static/js/dashboard.js"],
  "input_files": ["microblog/server/routes/api.py", "microblog/builder/markdown_processor.py", "templates/dashboard/post_edit.html"],
  "deliverables": "Live markdown preview, HTMX integration, debounced input handling, preview interface",
  "acceptance_criteria": "Preview updates in real-time with 500ms delay, markdown renders correctly, preview pane responsive, no performance issues",
  "dependencies": ["I5.T1", "I3.T2"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: key-interaction-flow (from 04_Behavior_and_Communication.md)

```markdown
**Key Interaction Flow (Sequence Diagram):**

**Description:** This diagram illustrates the complete workflow for user authentication and post creation, showing the interaction between the web browser, dashboard application, authentication system, and content storage.

== Live Preview Flow ==
author -> browser : Type in markdown editor
note right : 500ms debounce
browser -> dashboard : POST /api/preview (HTMX)
dashboard -> posts : Render markdown
posts -> dashboard : HTML preview
dashboard -> browser : HTML fragment
browser -> author : Live preview updated
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

### Context: task-i5-t3 (from 02_Iteration_I5.md)

```markdown
    *   **Task 5.3:**
        *   **Task ID:** `I5.T3`
        *   **Description:** Implement live markdown preview functionality with HTMX, debounced input handling, and real-time HTML rendering. Create preview pane in post editing interface.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** Live preview requirements, HTMX patterns, debouncing strategy, markdown rendering
        *   **Input Files:** ["microblog/server/routes/api.py", "microblog/builder/markdown_processor.py", "templates/dashboard/post_edit.html"]
        *   **Target Files:** ["microblog/server/routes/api.py", "templates/dashboard/post_edit.html", "static/js/dashboard.js"]
        *   **Deliverables:** Live markdown preview, HTMX integration, debounced input handling, preview interface
        *   **Acceptance Criteria:** Preview updates in real-time with 500ms delay, markdown renders correctly, preview pane responsive, no performance issues
        *   **Dependencies:** `I5.T1`, `I3.T2`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file contains HTMX API endpoints for dynamic post operations (create, update, delete, publish/unpublish). It follows a clear pattern of returning HTML fragments and includes proper error handling with helper functions `_create_error_fragment()` and `_create_success_fragment()`.
    *   **Recommendation:** You MUST add a new endpoint `/api/preview` to this file following the exact same pattern. The existing endpoints use Form data, proper authentication via `require_authentication()`, and CSRF protection. Import the markdown processor from `microblog.builder.markdown_processor` and use its `process_markdown_text()` method.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** This file provides a comprehensive markdown processing engine with frontmatter support, syntax highlighting, and content validation. It has a global singleton pattern with `get_markdown_processor()` function and includes methods like `process_markdown_text()` for converting raw markdown to HTML.
    *   **Recommendation:** You MUST import and use the `get_markdown_processor()` function and call its `process_markdown_text()` method for the preview functionality. This ensures consistency with the build system and maintains the same markdown rendering extensions.

*   **File:** `templates/dashboard/post_edit.html`
    *   **Summary:** This file contains a comprehensive post editing form with proper styling, JavaScript for slug generation, and a hidden preview panel (line 103-106) that's already scaffolded but not functional. It extends the dashboard layout and includes HTMX via the layout template.
    *   **Recommendation:** You MUST modify this file to make the preview panel functional. Add HTMX attributes to the content textarea (id="content" on line 85) with proper debouncing. The preview panel div already exists with id="markdown-preview" - you just need to make it visible and wire it up.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** This file includes HTMX library (line 19) and configures CSRF token handling for all HTMX requests (lines 148-155). It provides the base structure for all dashboard pages.
    *   **Recommendation:** The HTMX setup is already complete. You can rely on the existing CSRF token configuration and don't need to modify this file.

### Implementation Tips & Notes

*   **Tip:** The architecture documentation shows the exact HTMX pattern for live preview: `hx-trigger="keyup changed delay:500ms"` which provides the required 500ms debouncing.

*   **Tip:** I found that the preview panel HTML structure already exists in `post_edit.html` but is hidden with `style="display: none;"`. You just need to show it and wire up the HTMX functionality.

*   **Note:** The existing API endpoints in `api.py` all follow the same pattern: authentication check, form data parsing, service calls, and HTML fragment responses. Your preview endpoint should follow this same pattern.

*   **Warning:** The task mentions creating `static/js/dashboard.js` but I found that the `static/js/` directory is empty. You should create this file for any custom JavaScript that enhances the HTMX functionality, but the core preview functionality should work entirely through HTMX attributes.

*   **Tip:** The markdown processor has comprehensive error handling with `MarkdownProcessingError`. Make sure to catch these exceptions in your preview endpoint and return appropriate error fragments.

*   **Note:** The existing form submission in `post_edit.html` uses custom JavaScript (lines 282-325). You should ensure your preview functionality doesn't interfere with this existing behavior.

*   **Recommendation:** Follow the exact same HTML fragment response pattern as other API endpoints. Return raw HTML that can be inserted into the preview pane, not JSON responses.

*   **Security Note:** The preview endpoint should use the same authentication and CSRF protection patterns as existing endpoints. The `require_authentication()` middleware and CSRF token handling are already established patterns.