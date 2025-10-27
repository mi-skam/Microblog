# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T1",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Create configuration schema as JSON Schema file for validation of YAML configuration. Include all settings from specification with types, constraints, and descriptions.",
  "agent_type_hint": "DocumentationAgent",
  "inputs": "Configuration requirements from specification, YAML settings structure, validation rules",
  "target_files": ["docs/config_schema.json"],
  "input_files": ["microblog/server/config.py", "content/_data/config.yaml"],
  "deliverables": "Complete JSON Schema for configuration validation",
  "acceptance_criteria": "Schema validates all required settings, type constraints enforced, default values documented, validation errors are clear",
  "dependencies": ["I1.T4"],
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
*   **Data Model Overview:**
    *   **User**: Single admin user with credentials stored in SQLite (bcrypt hashed passwords)
    *   **Post**: Markdown files with YAML frontmatter containing title, date, slug, tags, draft status
    *   **Image**: Files stored in content/images/ with validation and build-time copying
    *   **Configuration**: YAML file with site settings, build options, server configuration, auth settings
    *   **Session**: Stateless JWT tokens in httpOnly cookies with configurable expiration
    *   *(Database ERD planned - see Iteration 1.T3)*
*   **API Contract Style:** RESTful HTTP API with HTMX enhancement for dynamic interactions, HTML-first responses for progressive enhancement
    *   *(Initial OpenAPI specification planned - see Iteration 2.T1)*
*   **Communication Patterns:**
    *   Synchronous HTTP request/response for page loads and API calls
    *   HTMX partial updates for dynamic content without full page refreshes
    *   File system events for configuration hot-reload in development mode
    *   Atomic file operations for build process with backup/rollback safety
    *   *(Key sequence diagrams planned - see Iteration 2.T2)*
```

### Context: task-i1-t4 (from 02_Iteration_I1.md)

```markdown
    <!-- anchor: task-i1-t4 -->
    *   **Task 1.4:**
        *   **Task ID:** `I1.T4`
        *   **Description:** Implement basic configuration management system with YAML parsing, validation, and environment-specific settings. Support hot-reload in development mode using file watchers.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** Configuration schema from specification, hot-reload requirements, validation rules
        *   **Input Files:** ["pyproject.toml", "microblog/__init__.py"]
        *   **Target Files:** ["microblog/server/config.py", "content/_data/config.yaml", "docs/config_schema.json"]
        *   **Deliverables:** Configuration manager class, default configuration file, JSON schema for validation, file watcher implementation
        *   **Acceptance Criteria:** Configuration loads from YAML successfully, validation catches invalid settings, hot-reload works in development mode, default config includes all required settings
        *   **Dependencies:** `I1.T1`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains a complete configuration management system with Pydantic models (SiteConfig, BuildConfig, ServerConfig, AuthConfig, AppConfig), validation, hot-reload support, and a `get_json_schema()` method that generates JSON schema from the Pydantic models.
    *   **Recommendation:** You MUST use the existing `AppConfig.model_json_schema()` method which already generates the complete JSON schema. The schema functionality already exists and is well-implemented.
*   **File:** `content/_data/config.yaml`
    *   **Summary:** This file contains the current YAML configuration with all required sections (site, build, server, auth) and proper structure.
    *   **Recommendation:** You SHOULD verify that the JSON schema accurately validates this existing configuration file.
*   **File:** `docs/config_schema.json`
    *   **Summary:** This file already exists and contains a complete JSON schema generated from the Pydantic models, including all required properties, constraints, and descriptions.
    *   **Recommendation:** You MUST verify this file is current and complete rather than recreating it. The schema appears to be generated automatically from the Pydantic models.

### Implementation Tips & Notes
*   **Tip:** The configuration system already includes a `get_json_schema()` method in the ConfigManager class that calls `AppConfig.model_json_schema()`. This method generates a complete JSON schema from the Pydantic model definitions.
*   **Note:** The existing JSON schema file at `docs/config_schema.json` appears to be complete and includes all required sections with proper validation rules, type constraints, and default values.
*   **Warning:** The task is marked as `"done": false` even though the deliverable exists. This suggests you need to verify completeness, ensure the schema validates the existing config, or update documentation about the schema.
*   **Critical Discovery:** The ConfigManager class has a `get_json_schema()` method (line 255-257) that should be used to ensure the schema file stays synchronized with the Pydantic models.
*   **Testing:** Comprehensive tests already exist in `tests/unit/test_config.py` including tests for `get_json_schema()` functionality (line 413-422).

### Verification Tasks Required
Since the JSON schema file already exists, your task should focus on:
1. **Verify Schema Completeness**: Ensure the existing schema covers all configuration settings
2. **Validate Against Current Config**: Test that the schema successfully validates the existing `config.yaml`
3. **Update Documentation**: Ensure the schema is properly documented and integrated
4. **Schema Generation Process**: Verify the schema can be regenerated from the Pydantic models
5. **Error Message Quality**: Ensure validation errors are clear and helpful