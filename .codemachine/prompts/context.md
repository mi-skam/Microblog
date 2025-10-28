# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T7",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Implement tag management with autocomplete functionality, tag creation, and tag-based post filtering. Create tag management interface in dashboard.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Tag management requirements, autocomplete functionality, filtering capabilities",
  "target_files": ["microblog/content/tag_service.py", "microblog/server/routes/api.py", "templates/dashboard/post_edit.html"],
  "input_files": ["microblog/content/post_service.py", "microblog/server/routes/api.py"],
  "deliverables": "Tag management service, autocomplete functionality, tag filtering, tag interface",
  "acceptance_criteria": "Tag autocomplete works during post editing, tag creation functional, post filtering by tags works, tag management interface intuitive",
  "dependencies": ["I5.T1", "I2.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

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
```

### Context: functional-requirements-summary (from 01_Context_and_Drivers.md)

```markdown
**Core Content Management:**
- Create, edit, and delete blog posts using markdown with YAML frontmatter
- Support draft and published post states with visibility controls
- Organize content using tag-based categorization system
- Upload and manage images with automatic build-time copying
```

### Context: task-i5-t7 (from 02_Iteration_I5.md)

```markdown
    *   **Task 5.7:**
        *   **Task ID:** `I5.T7`
        *   **Description:** Implement tag management with autocomplete functionality, tag creation, and tag-based post filtering. Create tag management interface in dashboard.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** Tag management requirements, autocomplete functionality, filtering capabilities
        *   **Input Files:** ["microblog/content/post_service.py", "microblog/server/routes/api.py"]
        *   **Target Files:** ["microblog/content/tag_service.py", "microblog/server/routes/api.py", "templates/dashboard/post_edit.html"]
        *   **Deliverables:** Tag management service, autocomplete functionality, tag filtering, tag interface
        *   **Acceptance Criteria:** Tag autocomplete works during post editing, tag creation functional, post filtering by tags works, tag management interface intuitive
        *   **Dependencies:** `I5.T1`, `I2.T4`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file contains the core PostService class with comprehensive CRUD operations for blog posts, including tag filtering via `list_posts(tag_filter=...)` method. Posts are stored as markdown files with YAML frontmatter.
    *   **Recommendation:** You MUST import and use the existing `get_post_service()` function. The `list_posts()` method already supports tag filtering - build upon this. The tags are stored as a list in post frontmatter.

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** Contains HTMX API endpoints for post operations with HTML fragment responses. Uses authentication middleware and follows established patterns for error handling and success responses.
    *   **Recommendation:** You MUST follow the existing patterns for HTMX endpoints. Import `require_authentication` from middleware, use `_create_error_fragment()` and `_create_success_fragment()` helpers. Return `HTMLResponse` objects.

*   **File:** `templates/dashboard/post_edit.html`
    *   **Summary:** Contains the post editing interface with HTMX integration for live preview, form submission, and validation. Tags are currently handled as a simple comma-separated input field (line 68-77).
    *   **Recommendation:** You MUST enhance the existing tags input field rather than replacing it. The current pattern expects comma-separated tags. Add HTMX attributes for autocomplete without breaking existing functionality.

*   **File:** `microblog/content/validators.py`
    *   **Summary:** Defines PostFrontmatter dataclass with `tags: list = field(default_factory=list)` for tag validation. No specific tag validation rules currently exist.
    *   **Recommendation:** Tags are stored as a simple list of strings in frontmatter. You SHOULD add tag validation utilities here if needed.

### Implementation Tips & Notes

*   **Tip:** The existing post service already has tag filtering built-in via `list_posts(tag_filter=str)` method (lines 312-353). This searches for tags case-insensitively and can be used for both filtering and autocomplete.

*   **Note:** HTMX endpoints in api.py follow a strict pattern: they require authentication, handle CSRF via middleware, return HTML fragments, and use specific error/success helper functions. You MUST follow this pattern.

*   **Warning:** The post edit template uses HTMX extensively for live preview and form submission. Ensure your tag autocomplete doesn't interfere with existing HTMX triggers or form submission logic.

*   **Architecture Pattern:** Posts are stored as individual markdown files with YAML frontmatter, not in a database. This means tag operations need to scan the filesystem. Consider caching strategies for performance.

*   **Existing Tag Handling:** Tags are currently parsed from comma-separated input and stored as lists in frontmatter. The post service handles tag filtering by lowercasing both the filter and post tags for case-insensitive matching.

*   **CSS Framework:** The project uses Pico.css as the base framework. Ensure any new UI elements follow Pico.css conventions for consistency.

*   **File Structure:** You need to create `microblog/content/tag_service.py` as a new file. Use the same patterns as other service files - provide a service class and a global getter function like `get_tag_service()`.

### Key Integration Points

*   **PostService Integration:** The tag service should work with the existing PostService to extract tags from all posts and provide aggregated tag operations.

*   **HTMX Integration:** Autocomplete functionality should use HTMX requests with debounced input (similar to the live preview pattern using `hx-trigger="keyup changed delay:500ms"`).

*   **Template Enhancement:** The post edit template needs minimal changes - enhance the existing tags input field with HTMX attributes for autocomplete display/interaction.

*   **API Endpoints:** Add new tag-related endpoints to api.py that return HTML fragments for autocomplete suggestions and tag management.