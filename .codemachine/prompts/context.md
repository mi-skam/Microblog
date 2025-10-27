# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T3",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Create dashboard layout template with Pico.css styling, navigation menu, authentication status, and responsive design. Implement base template structure for all dashboard pages.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Dashboard design requirements, Pico.css framework, responsive design principles",
  "target_files": ["templates/dashboard/layout.html", "static/css/dashboard.css"],
  "input_files": ["static/css/dashboard.css"],
  "deliverables": "Dashboard base template, CSS styling, responsive layout, navigation structure",
  "acceptance_criteria": "Template renders correctly, responsive design works on mobile, navigation functional, styling consistent with Pico.css",
  "dependencies": ["I1.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Architectural Style (from 02_Architecture_Overview.md)

```markdown
**Primary Style: Hybrid Static-First Architecture with Separation of Concerns**

The MicroBlog system employs a hybrid architectural approach that combines static site generation with a dynamic management interface. This design separates the public-facing blog (served as static files) from the administrative interface (dynamic web application), providing optimal performance for readers while maintaining ease of management for content creators.

**Key Architectural Patterns:**

1. **Static-First Generation**: The public blog is generated as static HTML files, ensuring maximum performance, security, and deployment flexibility. This eliminates runtime dependencies for content delivery and enables hosting on any static file server.

2. **Layered Monolith for Management**: The dashboard and build system follow a layered architecture pattern with clear separation between presentation (HTMX-enhanced web interface), business logic (content management and site generation), and data access (filesystem and SQLite) layers.

3. **Command-Query Separation**: Clear distinction between read operations (serving static content, dashboard views) and write operations (content modification, site rebuilds) with appropriate performance optimizations for each.

4. **Progressive Enhancement**: The dashboard uses HTMX for enhanced interactivity while maintaining functionality without JavaScript, ensuring accessibility and reliability.
```

### Context: Technology Stack Summary (from 02_Architecture_Overview.md)

```markdown
| **Component** | **Technology** | **Version** | **Justification** |
|---------------|----------------|-------------|-------------------|
| **Frontend Enhancement** | HTMX | 1.9+ (vendored) | Enables dynamic interactions without complex JavaScript frameworks. Maintains progressive enhancement principles. |
| **Styling** | Pico.css | Latest | Minimal, semantic CSS framework (<10KB) providing clean styling without design lock-in. |
| **Template Engine** | Jinja2 | Latest | Industry standard with excellent performance, template inheritance, and extensive filter ecosystem. Native FastAPI integration. |

**HTMX for Interactivity:**
- Maintains server-side rendering benefits while adding dynamic behavior
- Eliminates need for complex JavaScript build processes
- Provides excellent developer experience with minimal learning curve
- Graceful degradation ensures functionality without JavaScript
```

### Context: Task I4.T3 Details (from 02_Iteration_I4.md)

```markdown
**Task 4.3:**
* **Task ID:** `I4.T3`
* **Description:** Create dashboard layout template with Pico.css styling, navigation menu, authentication status, and responsive design. Implement base template structure for all dashboard pages.
* **Agent Type Hint:** `FrontendAgent`
* **Inputs:** Dashboard design requirements, Pico.css framework, responsive design principles
* **Input Files:** ["static/css/dashboard.css"]
* **Target Files:** ["templates/dashboard/layout.html", "static/css/dashboard.css"]
* **Deliverables:** Dashboard base template, CSS styling, responsive layout, navigation structure
* **Acceptance Criteria:** Template renders correctly, responsive design works on mobile, navigation functional, styling consistent with Pico.css
* **Dependencies:** `I1.T1`
* **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

* **File:** `templates/base.html`
  * **Summary:** This file contains the existing public-facing template structure with embedded CSS styling for the static blog site. It provides a good reference for the overall structure and styling approach, but is NOT for the dashboard.
  * **Recommendation:** You should NOT modify this file as it's for the public blog. Use it as inspiration for structure but create a completely separate dashboard template hierarchy.

* **File:** `microblog/server/app.py`
  * **Summary:** This file contains the FastAPI application factory with middleware configuration, static file mounting, and template directory setup. It shows how templates are configured.
  * **Recommendation:** You MUST understand that templates are configured via `app.state.templates = Jinja2Templates(directory=str(template_dir))` where template_dir is `content_dir / "templates"`. Your dashboard templates will be served from this system.

* **File:** `microblog/server/routes/auth.py`
  * **Summary:** This file contains existing authentication routes that reference template paths like "auth/login.html" and use the templates system for rendering.
  * **Recommendation:** You SHOULD follow the same pattern for template organization. Notice how templates are used: `templates.TemplateResponse("auth/login.html", {...})` with context variables.

* **File:** `microblog/server/middleware.py`
  * **Summary:** This file contains authentication middleware that protects dashboard routes and provides user context via `request.state.user` and CSRF token management.
  * **Recommendation:** You MUST design your template to work with the authentication system. The current user is available via `get_current_user(request)` and CSRF tokens via `get_csrf_token(request)`.

### Implementation Tips & Notes

* **Tip:** The project directory structure shows that `templates/dashboard/` directory exists but is empty. You need to create the layout template there.

* **Tip:** The `static/css/` directory exists but is empty. You need to create the dashboard.css file there. Notice that static files are served from the content directory's static folder, not the project root static folder.

* **Note:** The existing base.html template uses inline CSS. For the dashboard, you should use Pico.css as specified, which means you'll need to either vendor it or include it via CDN, then add your custom dashboard.css for additional styling.

* **Warning:** The authentication system expects templates in specific locations. The auth routes look for templates like "auth/login.html" relative to the templates directory. Your dashboard layout should be at "dashboard/layout.html".

* **Tip:** Based on the middleware code, authenticated users will have access to request.state.user containing user information. Your template should display authentication status and provide logout functionality.

* **Note:** The application is configured to redirect the root path ("/") to "/dashboard", so your dashboard layout will be the main interface users see after authentication.

* **Tip:** The project uses HTMX for interactivity as specified in the architecture. Your layout template should be prepared to include HTMX and support progressive enhancement patterns.

* **Critical:** The task specifies Pico.css styling, which is a semantic CSS framework. This means you should use semantic HTML elements and let Pico.css provide the base styling, then add custom CSS in dashboard.css for dashboard-specific enhancements.