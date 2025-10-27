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

### Context: data-model-overview (from 03_System_Structure_and_Data.md)

```markdown
### 3.6. Data Model Overview & ERD

**Description:** The MicroBlog system uses a hybrid data storage approach combining a lightweight SQLite database for user authentication with filesystem-based storage for content. This design minimizes external dependencies while providing structured access to different data types.

**Key Entities:**

1. **User**: Single admin user with authentication credentials (stored in SQLite)
2. **Post**: Blog posts with metadata and content (stored as markdown files with YAML frontmatter)
3. **Image**: Media files referenced in posts (stored in filesystem with metadata tracking)
4. **Configuration**: System settings and blog metadata (stored as YAML configuration file)
5. **Session**: Authentication sessions (stateless JWT tokens, no persistent storage)

**Post File Entity Structure:**
```
entity "Post File" as post {
  --
  **Frontmatter (YAML)**
  title : VARCHAR(200)
  date : DATE
  slug : VARCHAR(200) <<optional>>
  tags : ARRAY[VARCHAR]
  draft : BOOLEAN = false
  description : VARCHAR(300)
  --
  **Content (Markdown)**
  content : TEXT
  --
  **File Metadata**
  file_path : VARCHAR(500)
  created_at : TIMESTAMP
  modified_at : TIMESTAMP
}
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
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file contains the complete PostService class with comprehensive CRUD operations for blog posts. It handles markdown files with YAML frontmatter, validation, draft/publish workflows, and filesystem operations.
    *   **Recommendation:** You MUST import and use the `get_post_service()` function from this file. The PostService already implements all necessary backend operations including `create_post()`, `update_post()`, `get_post_by_slug()`, and validation. DO NOT reimplement these methods.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** This file provides the complete dashboard layout template with Pico.css styling, navigation, HTMX integration, and CSRF token handling.
    *   **Recommendation:** You MUST extend this layout template. The template already includes HTMX, CSRF token handling, navigation, and responsive design. Use the existing block structure including `{% block content %}`, `{% block extra_styles %}`, and `{% block extra_scripts %}`.

*   **File:** `microblog/server/routes/dashboard.py`
    *   **Summary:** This file contains existing dashboard routes including the post editing routes `new_post()` and `edit_post()` that are already implemented and reference the post_edit.html template.
    *   **Recommendation:** You MUST enhance this file by adding POST/PUT endpoints to handle form submissions. The GET routes are already implemented and working correctly with the post service.

*   **File:** `templates/dashboard/post_edit.html`
    *   **Summary:** This template is ALREADY FULLY IMPLEMENTED with complete form fields, styling, HTMX integration, JavaScript validation, and form handling.
    *   **Recommendation:** The template is complete and functional. You may need to review and ensure it meets all requirements, but major changes are not needed.

*   **File:** `microblog/content/validators.py`
    *   **Summary:** Contains PostFrontmatter and PostContent dataclasses with validation logic for blog posts including title, tags, dates, slugs, and content validation.
    *   **Recommendation:** You SHOULD use the `validate_post_content()` function for validating form submissions. These validators are already integrated with the PostService.

### Implementation Tips & Notes

*   **Tip:** The task requires implementing form handling for POST/PUT requests to create and update posts. The POST endpoint should be `/api/posts` and PUT should be `/api/posts/{slug}` as indicated in the existing template form action.

*   **Note:** The post_edit.html template already exists and is fully functional with proper form fields, CSRF protection, validation, and JavaScript. The template form submits to `/api/posts` (POST) and `/api/posts/{slug}` (PUT) endpoints.

*   **Warning:** The template expects API endpoints that handle form data, not JSON. The form uses `FormData` and expects server-side form processing, not JSON APIs.

*   **Critical:** You need to add the missing API routes for handling form submissions. The dashboard routes only handle GET requests for displaying forms, but POST/PUT handlers for `/api/posts` and `/api/posts/{slug}` are missing.

*   **Security:** CSRF tokens are already properly configured in the layout template and the post_edit form. Ensure all POST/PUT endpoints validate CSRF tokens using the existing middleware.

*   **Validation:** The PostService.create_post() and PostService.update_post() methods already handle validation and will raise appropriate exceptions (PostValidationError, PostFileError) that you should catch and handle in the API endpoints.

*   **Response Format:** Based on the template JavaScript, successful submissions should redirect to `/dashboard/posts`, while errors should return appropriate HTTP status codes with error messages.

*   **Templates Directory:** Note that the templates are using Jinja2Templates with directory `str(get_content_dir() / "templates")` in the dashboard routes, but the actual templates are in the root `templates/` directory. This may need to be corrected to use the proper template directory.