# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T4",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Implement asset manager for copying images and static files from content directory to build output. Handle file validation, path management, and build-time optimization.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Asset management requirements, file copying strategy, image handling specifications",
  "target_files": ["microblog/builder/asset_manager.py"],
  "input_files": ["microblog/server/config.py"],
  "deliverables": "Asset copying system, file validation, path management, static file handling",
  "acceptance_criteria": "Images copy correctly to build directory, file paths resolve properly, validation prevents invalid files, static assets handled",
  "dependencies": ["I1.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: task-i3-t4 (from 02_Iteration_I3.md)

```markdown
<!-- anchor: task-i3-t4 -->
*   **Task 3.4:**
    *   **Task ID:** `I3.T4`
    *   **Description:** Implement asset manager for copying images and static files from content directory to build output. Handle file validation, path management, and build-time optimization.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Asset management requirements, file copying strategy, image handling specifications
    *   **Input Files:** ["microblog/server/config.py"]
    *   **Target Files:** ["microblog/builder/asset_manager.py"]
    *   **Deliverables:** Asset copying system, file validation, path management, static file handling
    *   **Acceptance Criteria:** Images copy correctly to build directory, file paths resolve properly, validation prevents invalid files, static assets handled
    *   **Dependencies:** `I1.T4`
    *   **Parallelizable:** Yes
```

### Context: directory-structure (from 01_Plan_Overview_and_Setup.md)

```markdown
<!-- anchor: directory-structure -->
## 3. Directory Structure

*   **Root Directory:** `microblog/`
*   **Structure Definition:** Organized for clear separation of concerns with dedicated locations for source code, templates, content, and generated artifacts.

~~~
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
├── static/                         # Static assets for dashboard and site
│   ├── css/
│   │   ├── dashboard.css           # Dashboard-specific styles
│   │   └── site.css                # Public site styles (Pico.css based)
│   ├── js/
│   │   ├── htmx.min.js             # Vendored HTMX library
│   │   └── dashboard.js            # Minimal dashboard JavaScript
│   └── images/
│       └── favicon.ico             # Site favicon
~~~
```

### Context: data-storage-strategy (from 03_System_Structure_and_Data.md)

```markdown
<!-- anchor: data-storage-strategy -->
**Data Storage Strategy:**

**File System Storage (content/):**
- Markdown files with YAML frontmatter for posts
- Images stored in organized directory structure
- Configuration as human-readable YAML
- Version control friendly (Git integration possible)
- Direct file system access for build process

**Generated Output (build/):**
- Static HTML, CSS, and JavaScript files
- Copied and optimized images
- RSS feed and sitemap generation
- Atomic generation with backup/rollback
- Deployable to any static file server

**Performance Considerations:**
- File system operations optimized for sequential reading during builds
- SQLite provides excellent performance for single-user authentication
- Content directory structure designed for efficient traversal
- Build output optimized for CDN and static hosting performance
```

### Context: core-architecture (from 01_Plan_Overview_and_Setup.md)

```markdown
<!-- anchor: core-architecture -->
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
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains the comprehensive configuration management system with YAML parsing, validation, and hot-reload support. It defines `BuildConfig` with `output_dir` and `backup_dir` settings.
    *   **Recommendation:** You MUST import and use the `get_config()` function to access build directory paths. The `BuildConfig` provides `output_dir` (defaults to 'build') and `backup_dir` (defaults to 'build.bak') settings.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file contains shared utilities including directory management and path helpers. It provides `ensure_directory()`, `safe_copy_file()`, and path getter functions.
    *   **Recommendation:** You SHOULD reuse the existing `safe_copy_file()` and `ensure_directory()` functions. The file also provides `get_content_dir()`, `get_build_dir()`, and `get_static_dir()` path helpers that you MUST use for consistency.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** This file shows the established pattern for builder components with error handling, logging, and global instance management.
    *   **Recommendation:** You MUST follow the same architectural pattern: create an `AssetManagingError` exception class, use comprehensive logging, and provide a global `get_asset_manager()` function.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** This file demonstrates the builder module pattern with initialization, error handling, and integration with the configuration system.
    *   **Recommendation:** You SHOULD follow the same initialization pattern and integrate with the configuration system using `get_config()`.

### Implementation Tips & Notes

*   **Tip:** I found the build process sequence diagram at `docs/diagrams/build_process.puml` shows the asset manager is called during the "Asset Copying Phase" by the Build Management Service. Your asset manager will be invoked as part of the atomic build workflow.

*   **Note:** The configuration file at `content/_data/config.yaml` shows the build settings structure. The asset manager needs to handle copying from multiple sources: `content/images/` (user uploads) and `static/` (dashboard assets) to the build output directory.

*   **Tip:** The directory structure shows that images go to `content/images/` and static assets are in `static/`. Both need to be copied to the build directory with proper organization.

*   **Warning:** The build process diagram emphasizes atomic operations with backup/rollback. Your asset manager MUST support the atomic build pattern - if copying fails at any point, the build system should be able to rollback cleanly.

*   **Pattern:** All builder modules follow the pattern: `SomeBuilderError` exception class, logging, initialization with config, and a global getter function like `get_asset_manager()`.

*   **Security:** File validation is mentioned in the acceptance criteria. You SHOULD implement validation to prevent copying of dangerous file types or files outside expected locations.

*   **Performance:** The architecture emphasizes build performance targets (<5s for 100 posts). Your asset copying should be efficient and only copy files that have changed when possible.