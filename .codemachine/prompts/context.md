# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T4",
  "iteration_id": "I1",
  "iteration_goal": "Establish project foundation, directory structure, core architecture documentation, and basic CLI framework",
  "description": "Implement basic configuration management system with YAML parsing, validation, and environment-specific settings. Support hot-reload in development mode using file watchers.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Configuration schema from specification, hot-reload requirements, validation rules",
  "target_files": ["microblog/server/config.py", "content/_data/config.yaml", "docs/config_schema.json"],
  "input_files": ["pyproject.toml", "microblog/__init__.py"],
  "deliverables": "Configuration manager class, default configuration file, JSON schema for validation, file watcher implementation",
  "acceptance_criteria": "Configuration loads from YAML successfully, validation catches invalid settings, hot-reload works in development mode, default config includes all required settings",
  "dependencies": ["I1.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Configuration Manager Definition (from 01_Plan_Overview_and_Setup.md)

```markdown
**Configuration Manager**: YAML-based settings with validation and hot-reload support
```

### Context: Configuration Data Model (from 01_Plan_Overview_and_Setup.md)

```markdown
**Configuration**: YAML file with site settings, build options, server configuration, auth settings
```

### Context: Configuration Hot-Reload Requirements (from 01_Plan_Overview_and_Setup.md)

```markdown
Configuration hot-reload in development mode
File Watching: watchfiles for development mode configuration hot-reload
File system events for configuration hot-reload in development mode
```

### Context: Directory Structure for Configuration (from 01_Plan_Overview_and_Setup.md)

```markdown
├── content/                        # User content directory (runtime)
│   ├── posts/                      # Markdown blog posts
│   ├── pages/                      # Static pages (about, contact, etc.)
│   ├── images/                     # User-uploaded images
│   └── _data/
│       └── config.yaml             # Site configuration
```

### Context: Configuration Schema Requirements (from 01_Plan_Overview_and_Setup.md)

```markdown
**Configuration Schema (JSON Schema)** - To validate YAML configuration files and document settings *(Created in I4.T1)*
```

### Context: Configuration File Structure from ERD (from database_erd.puml)

```markdown
entity "Config File" as config {
  --
  **Site Settings**
  site.title : VARCHAR(200)
  site.url : VARCHAR(500)
  site.author : VARCHAR(200)
  site.description : VARCHAR(500)
  --
  **Build Settings**
  build.output_dir : VARCHAR(100)
  build.backup_dir : VARCHAR(100)
  build.posts_per_page : INTEGER
  --
  **Server Settings**
  server.host : VARCHAR(100)
  server.port : INTEGER
  server.hot_reload : BOOLEAN
  --
  **Auth Settings**
  auth.jwt_secret : VARCHAR(255)
  auth.session_expires : INTEGER
}
```

### Context: Configuration Management Component (from component_diagram.puml)

```markdown
Component(config_manager, "Configuration Manager", "YAML File Access", "Loads and validates configuration")

Rel(config_manager, content_store, "Reads config", "YAML parsing")

note top of config : YAML file: content/_data/config.yaml
                    Validated on application start
                    Hot-reload in dev mode
```

### Context: Detailed Configuration Schema and Validation from Architecture Research

```markdown
# Config (YAML File) Structure
site:
  title: (REQUIRED, string)
  url: (REQUIRED, string, valid URL)
  author: (REQUIRED, string)
  description: (OPTIONAL, string)

build:
  output_dir: (REQUIRED, string, default='build')
  backup_dir: (REQUIRED, string, default='build.bak')
  posts_per_page: (REQUIRED, integer, default=10)

server:
  host: (REQUIRED, string, default='127.0.0.1')
  port: (REQUIRED, integer, 1024-65535)
  hot_reload: (REQUIRED, boolean, default=false, dev-only)

auth:
  jwt_secret: (REQUIRED, string, min 32 chars)
  session_expires: (REQUIRED, integer, seconds, default=7200)
```

### Context: Hot-Reload Behavior Requirements

```markdown
**Development Mode**: Config file changes → app **SHOULD** detect change via file watcher → reload configuration → log reload event
**Production Mode**: Config file changes → app **MUST** require manual server restart to apply changes
**Error Handling**: Config file invalid → app **MUST** log error and keep previous valid config
```

### Context: Performance and Validation Requirements

```markdown
**NFR-PERF-005**: Config file changes **MUST** be detected and applied within 2 seconds (dev mode)
**Startup Validation**: Complete build validation before activation
**Schema Validation**: JSON Schema validation and comprehensive setting coverage
**Error Handling**: Invalid Config File → App **MUST** refuse to start with detailed validation errors
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `pyproject.toml`
    *   **Summary:** This file contains the complete Python project configuration with all required dependencies already specified.
    *   **Recommendation:** You SHOULD use the existing dependencies: `pyyaml>=6.0.0` for YAML parsing, `watchfiles>=0.20.0` for file watching, and `pydantic>=2.0.0` for validation models.

*   **File:** `microblog/__init__.py`
    *   **Summary:** This file contains the package initialization with version information and basic metadata.
    *   **Recommendation:** You SHOULD import and use the `__version__` constant if needed in configuration management.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file contains utility functions including `get_project_root()`, `get_content_dir()`, and `ensure_directory()` helpers.
    *   **Recommendation:** You MUST use `get_content_dir()` to locate the configuration file at `content/_data/config.yaml` and `ensure_directory()` to create directories as needed.

*   **File:** `microblog/cli.py`
    *   **Summary:** This file contains the Click-based CLI interface with basic command structure already implemented.
    *   **Recommendation:** You can reference this file to understand the project's CLI patterns, but configuration management should be independent and importable from other modules.

*   **File:** `microblog/server/__init__.py`
    *   **Summary:** This file is the package initialization for the server components.
    *   **Recommendation:** Your configuration manager (`microblog/server/config.py`) will be a new module in this existing package structure.

*   **File:** `docs/diagrams/component_diagram.puml` and `docs/diagrams/database_erd.puml`
    *   **Summary:** These files contain the PlantUML diagrams showing the Configuration Manager component and Config File entity specifications.
    *   **Recommendation:** You MUST implement the configuration manager to match the specifications in these diagrams, including YAML file access and validation capabilities.

### Implementation Tips & Notes
*   **Tip:** The project already has a well-defined directory structure. The configuration file MUST be placed at `content/_data/config.yaml` as shown in the ERD diagram.
*   **Note:** The component diagram shows that the Configuration Manager should have "YAML File Access" capabilities and should "Load and validate configuration". This indicates you need both parsing and validation functionality.
*   **Warning:** The hot-reload functionality is ONLY for development mode. You MUST ensure that production mode requires manual server restart for configuration changes.
*   **Tip:** The task requires creating three specific files: `microblog/server/config.py` (the manager class), `content/_data/config.yaml` (default config), and `docs/config_schema.json` (JSON schema for validation).
*   **Note:** The architecture research shows that configuration validation should happen at startup and refuse to start with detailed errors if invalid. You MUST implement comprehensive validation.
*   **Warning:** JWT secret MUST be minimum 32 characters according to the specification. This should be enforced in your validation.
*   **Tip:** Port validation should enforce the range 1024-65535 as specified in the configuration schema requirements.
*   **Note:** The existing dependencies in `pyproject.toml` include all the libraries you need: `pyyaml` for YAML parsing, `watchfiles` for file watching, and `pydantic` for validation models.