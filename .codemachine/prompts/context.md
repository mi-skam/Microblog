# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T5",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Integrate build system with dashboard, adding build trigger endpoints, progress tracking, and status updates with HTMX. Implement build queue and background processing.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Build system integration, progress tracking, background processing requirements",
  "target_files": ["microblog/server/routes/api.py", "microblog/server/build_service.py"],
  "input_files": ["microblog/builder/generator.py", "microblog/server/routes/api.py"],
  "deliverables": "Build trigger endpoints, progress tracking, status updates, background processing, build queue",
  "acceptance_criteria": "Builds trigger from dashboard, progress shows in real-time, status updates work, background processing functional, build queue prevents conflicts",
  "dependencies": ["I5.T1", "I3.T5"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: task-i5-t5 (from 02_Iteration_I5.md)

```markdown
<!-- anchor: task-i5-t5 -->
*   **Task 5.5:**
    *   **Task ID:** `I5.T5`
    *   **Description:** Integrate build system with dashboard, adding build trigger endpoints, progress tracking, and status updates with HTMX. Implement build queue and background processing.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Build system integration, progress tracking, background processing requirements
    *   **Input Files:** ["microblog/builder/generator.py", "microblog/server/routes/api.py"]
    *   **Target Files:** ["microblog/server/routes/api.py", "microblog/server/build_service.py"]
    *   **Deliverables:** Build trigger endpoints, progress tracking, status updates, background processing, build queue
    *   **Acceptance Criteria:** Builds trigger from dashboard, progress shows in real-time, status updates work, background processing functional, build queue prevents conflicts
    *   **Dependencies:** `I5.T1`, `I3.T5`
    *   **Parallelizable:** Yes
```

### Context: api-design-communication (from 04_Behavior_and_Communication.md)

```markdown
<!-- anchor: api-design-communication -->
### 3.7. API Design & Communication

<!-- anchor: api-style -->
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
<!-- anchor: htmx-integration -->
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

### Context: key-architectural-artifacts (from 01_Plan_Overview_and_Setup.md)

```markdown
<!-- anchor: key-architectural-artifacts -->
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** This file contains the complete BuildGenerator class with atomic build operations, progress tracking via BuildProgress callbacks, and comprehensive error handling. It supports progress callbacks and already has BuildPhase enums and BuildResult data structures.
    *   **Recommendation:** You MUST import and use the `BuildGenerator`, `BuildProgress`, `BuildPhase`, and `BuildResult` classes from this file. The generator already supports progress callbacks - leverage this for real-time updates.

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file contains existing HTMX API endpoints for post operations, image uploads, and markdown preview. It uses HTML fragments for responses and includes proper authentication and error handling patterns.
    *   **Recommendation:** You SHOULD follow the existing patterns in this file for new build endpoints. Use the `_create_error_fragment()` and `_create_success_fragment()` helper functions for consistent HTML responses.

*   **File:** `microblog/cli.py`
    *   **Summary:** This file shows how builds are currently triggered via CLI with progress callbacks. The `perform_build()` function demonstrates how to use the build_site() function with progress tracking.
    *   **Recommendation:** You SHOULD adapt the progress callback pattern from the CLI for web-based progress tracking. The CLI already shows how to handle BuildResult objects and display progress information.

### Implementation Tips & Notes

*   **Tip:** The BuildGenerator class already supports progress callbacks via the `progress_callback` parameter. You can use this to create real-time progress updates for HTMX. The callback receives BuildProgress objects with phase, message, percentage, and details.

*   **Note:** The existing API endpoints in `api.py` all follow a consistent pattern: authentication via `require_authentication(request)`, CSRF protection handled by middleware, and HTML fragment responses. Your build endpoints MUST follow this same pattern.

*   **Warning:** The task requires implementing `microblog/server/build_service.py` as a NEW file. This should handle background processing and build queue management. Consider using Python's asyncio or threading for background processing.

*   **Tip:** The existing HTMX patterns show the use of `hx-indicator`, `hx-target`, and `hx-swap-oob` attributes. For build progress, you'll likely need to use polling or server-sent events to update progress in real-time.

*   **Note:** Based on the existing code patterns, your build endpoints should return HTML fragments that can update specific DOM elements. Consider creating progress indicators that show build phases and completion percentages.

*   **Warning:** The current build system is synchronous and can take several seconds. You MUST implement background processing to prevent blocking the web interface. Consider using a queue system to prevent multiple simultaneous builds.

*   **Tip:** The BuildProgress objects contain `phase`, `message`, `percentage`, and optional `details`. These can be directly translated into HTML progress indicators for the dashboard.