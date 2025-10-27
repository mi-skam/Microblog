# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T1",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Create build process sequence diagram showing atomic build workflow with backup creation, content processing, template rendering, and rollback mechanisms. Document the complete build safety strategy.",
  "agent_type_hint": "DiagrammingAgent",
  "inputs": "Build process requirements, atomic build strategy, backup/rollback mechanisms",
  "target_files": ["docs/diagrams/build_process.puml"],
  "input_files": [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"],
  "deliverables": "PlantUML sequence diagram showing complete build workflow",
  "acceptance_criteria": "Diagram shows atomic build process, backup creation illustrated, rollback mechanism documented, all build steps included",
  "dependencies": ["I2.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: architectural-style (from 02_Architecture_Overview.md)

```markdown
**Primary Style: Hybrid Static-First Architecture with Separation of Concerns**

The MicroBlog system employs a hybrid architectural approach that combines static site generation with a dynamic management interface. This design separates the public-facing blog (served as static files) from the administrative interface (dynamic web application), providing optimal performance for readers while maintaining ease of management for content creators.

**Key Architectural Patterns:**

1. **Static-First Generation**: The public blog is generated as static HTML files, ensuring maximum performance, security, and deployment flexibility. This eliminates runtime dependencies for content delivery and enables hosting on any static file server.

2. **Layered Monolith for Management**: The dashboard and build system follow a layered architecture pattern with clear separation between presentation (HTMX-enhanced web interface), business logic (content management and site generation), and data access (filesystem and SQLite) layers.

3. **Command-Query Separation**: Clear distinction between read operations (serving static content, dashboard views) and write operations (content modification, site rebuilds) with appropriate performance optimizations for each.

4. **Progressive Enhancement**: The dashboard uses HTMX for enhanced interactivity while maintaining functionality without JavaScript, ensuring accessibility and reliability.

**Rationale for Architectural Choice:**

- **Performance**: Static files provide sub-100ms page loads and can handle high traffic without server resources
- **Simplicity**: Monolithic dashboard avoids distributed system complexity while maintaining clear internal boundaries
- **Deployment Flexibility**: Static output can be deployed anywhere (CDN, static hosts, traditional servers)
- **Developer Experience**: Clear separation enables focused development on each concern without cross-cutting complexity
- **Reliability**: Atomic builds with rollback capabilities ensure consistent site state
- **Security**: Static content eliminates many attack vectors; dynamic interface has minimal surface area
```

### Context: core-architecture (from 01_Plan_Overview_and_Setup.md)

```markdown
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
    *   **Image Management Service**: Upload, validation, and organization of media files
    *   **Build Management Service**: Orchestrates site generation with backup and rollback capabilities
    *   **CLI Interface**: Commands for build, serve, user creation, and system management
    *   **Configuration Manager**: YAML-based settings with validation and hot-reload support
```

### Context: task-i3-t1 (from 02_Iteration_I3.md)

```markdown
*   **Task 3.1:**
    *   **Task ID:** `I3.T1`
    *   **Description:** Create build process sequence diagram showing atomic build workflow with backup creation, content processing, template rendering, and rollback mechanisms. Document the complete build safety strategy.
    *   **Agent Type Hint:** `DiagrammingAgent`
    *   **Inputs:** Build process requirements, atomic build strategy, backup/rollback mechanisms
    *   **Input Files:** [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"]
    *   **Target Files:** ["docs/diagrams/build_process.puml"]
    *   **Deliverables:** PlantUML sequence diagram showing complete build workflow
    *   **Acceptance Criteria:** Diagram shows atomic build process, backup creation illustrated, rollback mechanism documented, all build steps included
    *   **Dependencies:** `I2.T4`
    *   **Parallelizable:** Yes
```

### Context: directory-structure (from 01_Plan_Overview_and_Setup.md)

```markdown
microblog/
├── microblog/                      # Main Python package
│   ├── builder/                    # Static site generation
│   │   ├── __init__.py
│   │   ├── generator.py            # Main build orchestration
│   │   ├── markdown_processor.py   # Markdown parsing and frontmatter
│   │   ├── template_renderer.py    # Jinja2 template rendering
│   │   └── asset_manager.py        # Image and static file copying
├── content/                        # User content directory (runtime)
│   ├── posts/                      # Markdown blog posts
│   ├── pages/                      # Static pages (about, contact, etc.)
│   ├── images/                     # User-uploaded images
│   └── _data/
│       └── config.yaml             # Site configuration
├── build/                          # Generated static site (gitignored)
├── build.bak/                      # Build backup directory (gitignored)
```

### Context: project-overview (from 01_Plan_Overview_and_Setup.md)

```markdown
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/__init__.py`
    *   **Summary:** Package initialization for static site generation components. Contains basic documentation about the module's purpose.
    *   **Recommendation:** This is the target directory for your diagram output. The builder package already exists and is properly set up.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** Comprehensive post service implementing CRUD operations for markdown posts with YAML frontmatter. Contains file system operations, validation, and error handling.
    *   **Recommendation:** Your sequence diagram MUST reference this service as it handles the content processing step of the build workflow. Import the PostService class to understand post loading/validation patterns.

*   **File:** `microblog/server/config.py`
    *   **Summary:** Configuration management system with YAML parsing, validation, hot-reload, and Pydantic models for BuildConfig including backup_dir and output_dir settings.
    *   **Recommendation:** Your diagram MUST show the configuration loading step as it provides build directories (build/ and build.bak/). The BuildConfig class defines backup_dir='build.bak' and output_dir='build'.

*   **File:** `docs/diagrams/component_diagram.puml`
    *   **Summary:** Existing PlantUML component diagram showing dashboard application architecture with Build Management Service component.
    *   **Recommendation:** Use the same PlantUML syntax and styling. Note that a "Build Management Service" component is already defined - your sequence diagram should show the detailed workflow this service orchestrates.

*   **File:** `docs/diagrams/database_erd.puml`
    *   **Summary:** Database ERD showing file system entities including Post Files and Config Files with their structure and metadata.
    *   **Recommendation:** Your sequence diagram should reference these entities as data sources for the build process. Posts are stored as .md files in content/posts/, and config is in content/_data/config.yaml.

### Implementation Tips & Notes

*   **Tip:** The codebase already has a clear builder package structure (`microblog/builder/`) that will house the actual implementation components referenced in the sequence diagram.

*   **Note:** The project uses a specific directory structure where `content/` contains source materials, `build/` is the output directory, and `build.bak/` is the backup location. Your diagram MUST show these exact paths.

*   **Warning:** The PostService already implements comprehensive file operations and validation. Your diagram should show how the build process leverages this existing service rather than duplicating file operations.

*   **Convention:** Existing PlantUML diagrams use C4 model includes (`!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml`). Follow the same pattern for consistency.

*   **Key Build Requirements:** Based on the configuration and existing code, the atomic build process must:
    1. Create backup of existing build/ directory to build.bak/
    2. Load configuration from content/_data/config.yaml
    3. Process markdown posts from content/posts/ using PostService
    4. Render templates to HTML (future components)
    5. Copy assets from content/images/ (future components)
    6. Atomically replace build/ directory or rollback on failure

*   **Safety Strategy:** The diagram must show error handling at each step with rollback to build.bak/ if any step fails, ensuring the build directory is never left in a broken state.