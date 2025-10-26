# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T2",
  "iteration_id": "I1",
  "iteration_goal": "Establish project foundation, directory structure, core architecture documentation, and basic CLI framework",
  "description": "Generate component diagram showing the internal structure of the Dashboard Web Application container, illustrating the layered architecture with routes, middleware, services, and repositories. Use PlantUML format for version control compatibility.",
  "agent_type_hint": "DiagrammingAgent",
  "inputs": "Component architecture description from Section 2, service separation patterns, FastAPI application structure",
  "target_files": ["docs/diagrams/component_diagram.puml"],
  "input_files": [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"],
  "deliverables": "PlantUML component diagram file showing dashboard application architecture",
  "acceptance_criteria": "PlantUML file renders correctly without syntax errors, diagram accurately reflects component relationships described in architecture section, all major services and their interactions are visible",
  "dependencies": ["I1.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: component-diagram (from 03_System_Structure_and_Data.md)

```markdown
### 3.5. Component Diagram(s) (C4 Level 3 - Dashboard Web App)

**Description:** This diagram shows the internal components of the Dashboard Web App container, illustrating the layered architecture with clear separation between web interface, business logic, and data access concerns.

**Diagram (PlantUML):**
```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

LAYOUT_WITH_LEGEND()

Container(dashboard_app, "Dashboard Web App", "FastAPI + HTMX", "Content management interface") {
    Component(auth_routes, "Authentication Routes", "FastAPI Router", "Handles login, logout, and session management")
    Component(dashboard_routes, "Dashboard Routes", "FastAPI Router", "Serves HTML pages for post management")
    Component(api_routes, "HTMX API Routes", "FastAPI Router", "Handles AJAX requests for dynamic interactions")

    Component(auth_middleware, "Auth Middleware", "FastAPI Middleware", "Validates JWT tokens and protects routes")
    Component(csrf_middleware, "CSRF Middleware", "FastAPI Middleware", "Prevents cross-site request forgery")

    Component(post_service, "Post Management Service", "Python Service", "Business logic for post CRUD operations")
    Component(build_service, "Build Management Service", "Python Service", "Orchestrates static site generation")
    Component(image_service, "Image Management Service", "Python Service", "Handles image upload and organization")

    Component(content_repository, "Content Repository", "File System Access", "Reads/writes markdown files and images")
    Component(user_repository, "User Repository", "SQLite Access", "Manages user authentication data")
    Component(config_manager, "Configuration Manager", "YAML File Access", "Loads and validates configuration")
}

ContainerDb_Ext(user_db, "User Database", "SQLite")
ContainerDb_Ext(content_store, "Content Storage", "File System")
Container_Ext(static_generator, "Static Site Generator", "Python")

Rel(auth_routes, auth_middleware, "Uses")
Rel(dashboard_routes, auth_middleware, "Protected by")
Rel(api_routes, auth_middleware, "Protected by")
Rel(api_routes, csrf_middleware, "Protected by")

Rel(auth_routes, user_repository, "Authenticates")
Rel(dashboard_routes, post_service, "Uses")
Rel(api_routes, post_service, "Uses")
Rel(api_routes, build_service, "Uses")
Rel(api_routes, image_service, "Uses")

Rel(post_service, content_repository, "Uses")
Rel(build_service, static_generator, "Triggers")
Rel(image_service, content_repository, "Uses")

Rel(content_repository, content_store, "Accesses", "File I/O")
Rel(user_repository, user_db, "Queries", "SQLite")
Rel(config_manager, content_store, "Reads config", "YAML parsing")

note right of post_service : Handles post validation\nMarkdown processing\nDraft/publish logic
note right of build_service : Atomic builds\nBackup management\nProgress tracking
@enduml
```
```

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

### Context: directory-structure (from 01_Plan_Overview_and_Setup.md)

```markdown
## 3. Directory Structure

*   **Root Directory:** `microblog/`
*   **Structure Definition:** Organized for clear separation of concerns with dedicated locations for source code, templates, content, and generated artifacts.

~~~
microblog/
├── microblog/                      # Main Python package
│   ├── __init__.py
│   ├── builder/                    # Static site generation
│   │   ├── __init__.py
│   │   ├── generator.py            # Main build orchestration
│   │   ├── markdown_processor.py   # Markdown parsing and frontmatter
│   │   ├── template_renderer.py    # Jinja2 template rendering
│   │   └── asset_manager.py        # Image and static file copying
│   ├── server/                     # Web application and dashboard
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI application setup
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── dashboard.py        # Dashboard page routes
│   │   │   └── api.py              # HTMX API endpoints
│   │   ├── middleware.py           # Auth and CSRF middleware
│   │   ├── models.py               # Pydantic request/response models
│   │   └── config.py               # Configuration management
│   ├── auth/                       # Authentication and user management
│   │   ├── __init__.py
│   │   ├── models.py               # User SQLite model
│   │   ├── jwt_handler.py          # JWT token management
│   │   └── password.py             # Password hashing utilities
│   ├── content/                    # Content management services
│   │   ├── __init__.py
│   │   ├── post_service.py         # Post CRUD operations
│   │   ├── image_service.py        # Image upload and management
│   │   └── validators.py           # Content validation logic
│   ├── cli.py                      # Click-based CLI interface
│   └── utils.py                    # Shared utilities and helpers
~~~
```

### Context: key-components (from 01_Plan_Overview_and_Setup.md)

```markdown
*   **Key Components/Services:**
    *   **Authentication Service**: JWT-based single-user authentication with bcrypt password hashing
    *   **Content Management Service**: CRUD operations for posts with markdown processing and validation
    *   **Static Site Generator**: Template rendering and asset copying with atomic build process
    *   **Dashboard Web Application**: HTMX-enhanced interface for content management and live preview
    *   **Image Management Service**: Upload, validation, and organization of media files
    *   **Build Management Service**: Orchestrates site generation with backup and rollback capabilities
    *   **CLI Interface**: Commands for build, serve, user creation, and system management
    *   **Configuration Manager**: YAML-based settings with validation and hot-reload support
    *   *(Component Diagram planned - see Iteration 1.T2)*
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/__init__.py`
    *   **Summary:** Basic package initialization file with version and metadata.
    *   **Recommendation:** This file establishes the package structure. The component diagram should reflect the modular organization shown here.

*   **File:** `microblog/server/__init__.py`
    *   **Summary:** Web application package initialization describing FastAPI application, routes, middleware, and models.
    *   **Recommendation:** This is the main container that your component diagram will detail. Focus on this module's internal structure.

*   **File:** `microblog/server/routes/__init__.py`
    *   **Summary:** Route handlers package describing authentication, dashboard pages, and HTMX API endpoints.
    *   **Recommendation:** These represent the three main route components in your diagram: auth_routes, dashboard_routes, and api_routes.

*   **File:** `microblog/cli.py`
    *   **Summary:** Complete CLI implementation with Click framework, showing commands for build, serve, create-user, init, and status.
    *   **Recommendation:** This file shows the CLI interface component that will interact with the dashboard web app. Note it imports from `microblog.utils` for directory paths.

*   **File:** `microblog/utils.py`
    *   **Summary:** Shared utilities providing path management functions and file operations.
    *   **Recommendation:** This represents shared utilities that components will use. Include this as a utility component in your diagram.

### Implementation Tips & Notes

*   **Tip:** The project structure is already established and matches the architecture specification exactly. The `docs/diagrams/` directory exists but is empty, ready for your PlantUML file.

*   **Note:** The CLI already shows integration points with the server components (build, serve commands), indicating clear separation between CLI tool and web application containers.

*   **Architecture Pattern:** The existing code shows a clean layered monolith structure with separate packages for server, auth, content, and builder - exactly matching the component diagram specification.

*   **File Location:** Your target file should be `docs/diagrams/component_diagram.puml`. The diagrams directory already exists.

*   **PlantUML Requirements:** Use the C4 Component diagram format as shown in the architecture specification. Include the C4-PlantUML library and follow the exact component structure provided in the architectural context.

*   **Component Mapping:**
    - Routes map to `microblog/server/routes/` (auth.py, dashboard.py, api.py)
    - Services map to `microblog/content/` and `microblog/auth/` packages
    - Repositories represent data access layers for SQLite and filesystem
    - Middleware represents FastAPI middleware components

*   **Validation:** The PlantUML file must render without syntax errors and accurately represent the layered architecture with all components and relationships shown in the specification.