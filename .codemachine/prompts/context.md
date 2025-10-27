# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T5",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Create dashboard routes for main interface showing post listings, statistics, and build status. Implement server-rendered pages with basic CRUD functionality.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Dashboard interface requirements, post management needs, statistics display",
  "target_files": ["microblog/server/routes/dashboard.py", "templates/dashboard/posts_list.html"],
  "input_files": ["microblog/content/post_service.py", "templates/dashboard/layout.html"],
  "deliverables": "Dashboard routes, post listing interface, statistics display, basic CRUD pages",
  "acceptance_criteria": "Dashboard loads with post list, statistics show correctly, basic navigation works, authentication required for access",
  "dependencies": ["I4.T4", "I2.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: architectural-style (from 02_Architecture_Overview.md)

```markdown
### 3.1. Architectural Style

**Primary Style: Hybrid Static-First Architecture with Separation of Concerns**

The MicroBlog system employs a hybrid architectural approach that combines static site generation with a dynamic management interface. This design separates the public-facing blog (served as static files) from the administrative interface (dynamic web application), providing optimal performance for readers while maintaining ease of management for content creators.

**Key Architectural Patterns:**

1. **Static-First Generation**: The public blog is generated as static HTML files, ensuring maximum performance, security, and deployment flexibility. This eliminates runtime dependencies for content delivery and enables hosting on any static file server.

2. **Layered Monolith for Management**: The dashboard and build system follow a layered architecture pattern with clear separation between presentation (HTMX-enhanced web interface), business logic (content management and site generation), and data access (filesystem and SQLite) layers.

3. **Command-Query Separation**: Clear distinction between read operations (serving static content, dashboard views) and write operations (content modification, site rebuilds) with appropriate performance optimizations for each.

4. **Progressive Enhancement**: The dashboard uses HTMX for enhanced interactivity while maintaining functionality without JavaScript, ensuring accessibility and reliability.
```

### Context: technology-stack (from 02_Architecture_Overview.md)

```markdown
| **Component** | **Technology** | **Version** | **Justification** |
|---------------|----------------|-------------|-------------------|
| **Backend Language** | Python | 3.10+ | Excellent ecosystem for text processing, web frameworks, and CLI tools. Mature libraries for markdown, templating, and authentication. |
| **Web Framework** | FastAPI | 0.100+ | Modern async framework with automatic OpenAPI documentation, excellent type support, and built-in security features. Ideal for both API endpoints and traditional web pages. |
| **Template Engine** | Jinja2 | Latest | Industry standard with excellent performance, template inheritance, and extensive filter ecosystem. Native FastAPI integration. |
| **Frontend Enhancement** | HTMX | 1.9+ (vendored) | Enables dynamic interactions without complex JavaScript frameworks. Maintains progressive enhancement principles. |
| **Styling** | Pico.css | Latest | Minimal, semantic CSS framework (<10KB) providing clean styling without design lock-in. |
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

### Context: task-i4-t5 (from 02_Iteration_I4.md)

```markdown
*   **Task 4.5:**
    *   **Task ID:** `I4.T5`
    *   **Description:** Create dashboard routes for main interface showing post listings, statistics, and build status. Implement server-rendered pages with basic CRUD functionality.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Dashboard interface requirements, post management needs, statistics display
    *   **Input Files:** ["microblog/content/post_service.py", "templates/dashboard/layout.html"]
    *   **Target Files:** ["microblog/server/routes/dashboard.py", "templates/dashboard/posts_list.html"]
    *   **Deliverables:** Dashboard routes, post listing interface, statistics display, basic CRUD pages
    *   **Acceptance Criteria:** Dashboard loads with post list, statistics show correctly, basic navigation works, authentication required for access
    *   **Dependencies:** `I4.T4`, `I2.T4`
    *   **Parallelizable:** Yes
```

### Context: directory-structure (from 01_Plan_Overview_and_Setup.md)

```markdown
├── microblog/                      # Main Python package
│   ├── server/                     # Web application and dashboard
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── dashboard.py        # Dashboard page routes
│   │   │   └── api.py              # HTMX API endpoints
│   └── content/                    # Content management services
│       ├── post_service.py         # Post CRUD operations
├── templates/                      # Jinja2 templates for site generation
│   └── dashboard/                  # Dashboard-specific templates
│       ├── layout.html             # Dashboard base template
│       ├── login.html              # Authentication form
│       ├── posts_list.html         # Post management interface
│       ├── post_edit.html          # Post creation/editing form
│       └── settings.html           # Configuration management
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** Complete PostService class providing CRUD operations for blog posts with markdown files and YAML frontmatter. Contains methods for create_post, get_post_by_slug, update_post, delete_post, list_posts, publish_post, etc.
    *   **Recommendation:** You MUST import and use the `get_post_service()` function from this file. Use its methods like `list_posts()`, `get_published_posts()`, `get_draft_posts()` for displaying posts. The service handles all file operations and validation.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** Complete dashboard layout template with Pico.css styling, navigation menu, authentication status, HTMX configuration, and CSRF token management.
    *   **Recommendation:** You MUST extend this template in your posts_list.html. It provides the complete dashboard structure including navigation, breadcrumbs, flash messages, and HTMX configuration. Use blocks like `{% block content %}`, `{% block page_title %}`, `{% block breadcrumb_items %}`.

*   **File:** `microblog/server/app.py`
    *   **Summary:** FastAPI application factory with middleware configuration, route registration, security headers, and authentication middleware setup.
    *   **Recommendation:** You need to register your dashboard router in this file using `app.include_router()`. Follow the pattern used for the auth router on line 99.

*   **File:** `microblog/server/routes/auth.py`
    *   **Summary:** Complete authentication routes implementation showing proper FastAPI route patterns, template usage, CSRF validation, and middleware integration.
    *   **Recommendation:** Follow the same patterns for template rendering, CSRF token handling, and user authentication checking. Use `get_current_user(request)` and `get_csrf_token(request)` from middleware.

*   **File:** `microblog/content/validators.py`
    *   **Summary:** PostContent and PostFrontmatter dataclass models with validation, computed properties like `is_draft`, `computed_slug`, and `filename`.
    *   **Recommendation:** Use these models when working with post data. The PostContent objects returned by PostService have useful properties for display.

### Implementation Tips & Notes

*   **Tip:** The PostService already provides all necessary methods for listing posts. Use `list_posts(include_drafts=True)` for dashboard viewing since admin should see all posts.

*   **Note:** The dashboard layout template already includes HTMX and CSRF token configuration. Your routes should work seamlessly with this setup.

*   **Warning:** All dashboard routes must be protected by authentication. The authentication middleware is already configured to protect `/dashboard` paths, but ensure your routes check for authenticated users.

*   **Tip:** For statistics display, you can use the PostService methods to count published vs draft posts: `len(post_service.get_published_posts())` and `len(post_service.get_draft_posts())`.

*   **Note:** The project follows a pattern where templates are loaded from `get_content_dir() / "templates"`. Follow the existing pattern in auth.py for template initialization.

*   **Convention:** The codebase uses consistent error handling with try/catch blocks and proper HTTP status codes. Follow the patterns established in auth.py.

*   **Important:** The dashboard navigation in layout.html expects routes like `/dashboard`, `/dashboard/posts`, `/dashboard/pages`, `/dashboard/settings`. Your main dashboard route should be `/dashboard`.