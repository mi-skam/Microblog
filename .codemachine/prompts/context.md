# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T5",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Create main build generator that orchestrates the complete build process with atomic operations, backup creation, and rollback capability. Implement build status tracking and progress reporting.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Build orchestration requirements, atomic build strategy, safety mechanisms",
  "target_files": ["microblog/builder/generator.py"],
  "input_files": ["microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "microblog/builder/asset_manager.py", "docs/diagrams/build_process.puml"],
  "deliverables": "Build orchestrator, atomic build implementation, backup/rollback system, progress tracking",
  "acceptance_criteria": "Build completes atomically (success or rollback), backup created before build, rollback works on failure, progress tracking functional",
  "dependencies": ["I3.T2", "I3.T3", "I3.T4"],
  "parallelizable": false,
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

### Context: functional-requirements-summary (from 01_Context_and_Drivers.md)

```markdown
**Static Site Generation:**
- Parse markdown files and render them through Jinja2 templates
- Generate complete static HTML website in dedicated build directory
- Copy all media assets from content to build directory
- Create RSS feed for content syndication
- Implement atomic build process with backup and rollback capabilities
```

### Context: task-i3-t5 (from 02_Iteration_I3.md)

```markdown
*   **Task 3.5:**
    *   **Task ID:** `I3.T5`
    *   **Description:** Create main build generator that orchestrates the complete build process with atomic operations, backup creation, and rollback capability. Implement build status tracking and progress reporting.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Build orchestration requirements, atomic build strategy, safety mechanisms
    *   **Input Files:** ["microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "microblog/builder/asset_manager.py", "docs/diagrams/build_process.puml"]
    *   **Target Files:** ["microblog/builder/generator.py"]
    *   **Deliverables:** Build orchestrator, atomic build implementation, backup/rollback system, progress tracking
    *   **Acceptance Criteria:** Build completes atomically (success or rollback), backup created before build, rollback works on failure, progress tracking functional
    *   **Dependencies:** `I3.T2`, `I3.T3`, `I3.T4`
    *   **Parallelizable:** No
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** This file provides complete markdown processing with YAML frontmatter support, syntax highlighting, content validation, and error handling. It includes a global singleton instance via `get_markdown_processor()`.
    *   **Recommendation:** You MUST import and use the `get_markdown_processor()` function to get the global processor instance. The processor has methods like `process_content()`, `validate_and_process()`, and `process_file_content()` that your generator will need.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** This file provides Jinja2 template rendering with site-wide context management, RSS feed generation, and template validation. It includes methods for rendering different page types (homepage, posts, archives, tags, RSS).
    *   **Recommendation:** You MUST import and use the `get_template_renderer()` function to get the global renderer instance. Key methods include `render_homepage()`, `render_post()`, `render_archive()`, `render_tag_page()`, and `render_rss_feed()`.

*   **File:** `microblog/builder/asset_manager.py`
    *   **Summary:** This file handles copying images and static files from content directory to build output, with file validation, path management, and security checks. It supports multiple asset source mappings and efficient update detection.
    *   **Recommendation:** You MUST import and use the `get_asset_manager()` function to get the global asset manager instance. The main method you'll need is `copy_all_assets()` which returns a results dictionary with copy statistics.

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file provides configuration management with BuildConfig that includes `output_dir` and `backup_dir` settings. The BuildConfig has validation and defaults for build-related settings.
    *   **Recommendation:** You MUST import and use the `get_config()` function to access build configuration. The config has `config.build.output_dir` and `config.build.backup_dir` properties that are essential for your atomic build strategy.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file provides post management with CRUD operations for markdown posts, including methods to get published posts and handle post filtering.
    *   **Recommendation:** You SHOULD import and use `get_post_service()` to access post data. The service has `get_published_posts()` method which returns the posts that need to be built.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file provides utility functions including `ensure_directory()` for safe directory creation, path helpers like `get_project_root()`, and file operation utilities.
    *   **Recommendation:** You MUST import and use `ensure_directory()` for safe directory creation during the build process. Also use the path helper functions for consistent directory access.

*   **File:** `docs/diagrams/build_process.puml`
    *   **Summary:** This file contains the complete sequence diagram showing the atomic build workflow with backup creation, content processing, template rendering, and rollback mechanisms. It documents the complete build safety strategy.
    *   **Recommendation:** You MUST follow the sequence and safety strategy outlined in this diagram. It shows the precise order of operations and error handling that your generator must implement.

### Implementation Tips & Notes

*   **Tip:** The configuration system uses `BuildConfig` with `output_dir` (default: 'build') and `backup_dir` (default: 'build.bak') properties. These are essential for implementing the atomic build strategy.

*   **Note:** All three builder components (markdown_processor, template_renderer, asset_manager) use global singleton instances accessed via `get_*()` functions. Follow this pattern for consistency.

*   **Warning:** The atomic build strategy requires very careful directory management. You MUST create backup before starting, work in a fresh build directory, and only remove backup on successful completion. Any failure should trigger rollback from backup.

*   **Tip:** The build process diagram shows a specific sequence: Configuration → Backup Creation → Content Processing → Template Rendering → Asset Copying → Verification → Cleanup/Rollback. Your generator must follow this exact order.

*   **Note:** The asset manager's `copy_all_assets()` method returns a results dictionary with success/failure counts. You should use this for build status reporting and to detect copy failures.

*   **Warning:** The codebase uses comprehensive error handling and logging throughout. Your generator must follow the same patterns, logging all major steps and handling all exceptions gracefully.

*   **Tip:** The template renderer has methods for all page types needed: `render_homepage()`, `render_post()`, `render_archive()`, `render_tag_page()`, and `render_rss_feed()`. You'll need to orchestrate calls to all of these.

*   **Note:** The build process should be designed to be called both from CLI and from the dashboard. Consider how progress reporting and status updates will work in both contexts.