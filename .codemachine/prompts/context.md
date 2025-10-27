# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T7",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Add CLI serve command to start development and production servers with proper configuration, hot-reload support, and graceful shutdown handling.",
  "agent_type_hint": "BackendAgent",
  "inputs": "CLI framework, server configuration, development vs production modes",
  "target_files": ["microblog/cli.py"],
  "input_files": ["microblog/cli.py", "microblog/server/app.py"],
  "deliverables": "CLI serve command, development mode, production configuration, server management",
  "acceptance_criteria": "`microblog serve` starts server correctly, development mode has hot-reload, production mode is secure, graceful shutdown works",
  "dependencies": ["I4.T2"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

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
    *   **Image Management Service**: Upload, validation, and organization of media files
    *   **Build Management Service**: Orchestrates site generation with backup and rollback capabilities
    *   **CLI Interface**: Commands for build, serve, user creation, and system management
    *   **Configuration Manager**: YAML-based settings with validation and hot-reload support
    *   *(Component Diagram planned - see Iteration 1.T2)*
```

### Context: task-i4-t7 (from 02_Iteration_I4.md)

```markdown
*   **Task 4.7:**
    *   **Task ID:** `I4.T7`
    *   **Description:** Add CLI serve command to start development and production servers with proper configuration, hot-reload support, and graceful shutdown handling.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** CLI framework, server configuration, development vs production modes
    *   **Input Files:** ["microblog/cli.py", "microblog/server/app.py"]
    *   **Target Files:** ["microblog/cli.py"]
    *   **Deliverables:** CLI serve command, development mode, production configuration, server management
    *   **Acceptance Criteria:** `microblog serve` starts server correctly, development mode has hot-reload, production mode is secure, graceful shutdown works
    *   **Dependencies:** `I4.T2`
    *   **Parallelizable:** Yes
```

### Context: deployment-strategy (from 05_Operational_Architecture.md)

```markdown
**Deployment Strategy:**

**Option 1: Full Stack Deployment (Recommended for Dynamic Management)**
```
Internet → nginx/Caddy (443) → FastAPI Dashboard (8000)
                           ↓
                    Static Files (build/)
```

**Option 2: Hybrid Deployment (Recommended for Performance)**
```
Local: MicroBlog Dashboard (development/management)
   ↓ (build + rsync/deploy)
Remote: Static File Server (production/public)
```

**Option 3: Container Deployment**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["microblog", "serve", "--host", "0.0.0.0"]
```
```

### Context: target-environment (from 05_Operational_Architecture.md)

```markdown
**Target Environment:**

**Primary Deployment Options:**
1. **Development Environment**: Local workstation with hot-reload capabilities
2. **Self-Hosted VPS**: Linux server with manual deployment and management
3. **Hybrid Deployment**: Local dashboard with static output deployed to CDN
4. **Container Deployment**: Docker-based deployment for consistency
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/cli.py`
    *   **Summary:** This file contains the main Click-based CLI framework with commands for build, create-user, init, and status. The serve command exists but is currently a placeholder (lines 207-240).
    *   **Recommendation:** You MUST replace the placeholder serve command implementation starting at line 207. The current implementation only prints acknowledgment messages and needs to be replaced with actual uvicorn server startup logic.

*   **File:** `microblog/server/app.py`
    *   **Summary:** This file contains the FastAPI application factory with create_app(), get_app(), and get_dev_app() functions. It includes proper middleware configuration, startup/shutdown events, and hot-reload support for development mode.
    *   **Recommendation:** You MUST import and use the get_app() and get_dev_app() functions from this file. These functions return properly configured FastAPI applications for production and development respectively.

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains the ConfigManager class with hot-reload support and ServerConfig model that defines host, port, and hot_reload settings.
    *   **Recommendation:** You SHOULD use the get_config_manager() function to access server configuration settings like host and port. The configuration manager already supports hot-reload in development mode.

*   **File:** `pyproject.toml`
    *   **Summary:** This file shows that uvicorn[standard]>=0.23.0 is already included as a dependency, so uvicorn is available for the server implementation.
    *   **Recommendation:** You MUST use uvicorn.run() to start the server. Do not add additional dependencies as uvicorn is already available.

### Implementation Tips & Notes
*   **Tip:** The serve command should support both development and production modes. Use the --reload flag to enable development mode with hot-reload, and ensure production mode runs without debug features.
*   **Note:** The existing app.py file already has proper startup/shutdown event handlers and configuration hot-reload support for development mode. You just need to wire up the uvicorn server to use these applications.
*   **Warning:** The CLI command currently has placeholder TODO comments at lines 231-239. You need to completely replace this implementation with actual uvicorn server startup code.
*   **Tip:** Use uvicorn's built-in graceful shutdown handling by setting up proper signal handlers. Consider using uvicorn.run() with proper host/port configuration from the config manager.
*   **Note:** The config system already supports server.host and server.port settings, so you should read these from configuration and allow CLI options to override them.
*   **Important:** Follow the existing CLI pattern in the build command which uses verbose output, configuration overrides, and proper error handling with colored output using click.style().