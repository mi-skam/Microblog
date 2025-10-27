# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T7",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Create comprehensive tests for build system including markdown processing, template rendering, asset management, and atomic build operations. Test build failure and rollback scenarios.",
  "agent_type_hint": "TestingAgent",
  "inputs": "Build system implementation, testing requirements, failure scenario testing",
  "target_files": ["tests/unit/test_build_system.py", "tests/integration/test_build_process.py"],
  "input_files": ["microblog/builder/generator.py", "microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "tests/conftest.py"],
  "deliverables": "Comprehensive build system test suite with failure scenario testing",
  "acceptance_criteria": "All build components tested, atomic operations verified, rollback scenarios tested, test coverage >85%, performance tests included",
  "dependencies": ["I3.T5", "I3.T6"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: data-storage-strategy (from 03_System_Structure_and_Data.md)

```markdown
**Data Storage Strategy:**

**SQLite Database (microblog.db):**
- Stores single user authentication record
- Lightweight, serverless, no external dependencies
- Automatic schema creation on first run
- Handles concurrent read access (dashboard operations)

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

### Context: project-overview (from 01_Plan_Overview_and_Setup.md)

```markdown
## 1. Project Overview

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
*   **Key Assumptions:**
    *   Single-user design eliminates complex permission systems
    *   Content volume will not exceed 1,000 posts (performance tested)
    *   Users have basic familiarity with markdown syntax
    *   Full rebuild strategy is acceptable for target content volume
    *   Users will implement their own content backup strategy (Git recommended)
    *   Dashboard usage occurs on trusted networks (localhost or VPN)
    *   Images are pre-optimized before upload (no automatic compression)
    *   Filesystem has sufficient read/write permissions for operations
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `tests/unit/test_build_system.py`
    *   **Summary:** This file contains comprehensive unit tests for all build system components including BuildProgress, BuildResult, MarkdownProcessor, TemplateRenderer, AssetManager, and BuildGenerator. It includes extensive failure scenario testing and performance tests.
    *   **Recommendation:** The existing tests are already quite comprehensive (1993 lines) and well-structured. You should REVIEW this file carefully to understand the testing patterns and identify any gaps rather than starting from scratch.

*   **File:** `tests/integration/test_build_process.py`
    *   **Summary:** This file contains integration tests for the complete build process including realistic project structure creation, successful builds, empty content handling, template issues, backup/rollback, and performance timing.
    *   **Recommendation:** This file is also comprehensive (959 lines) and includes excellent integration testing patterns. You should REVIEW this file to identify any missing edge cases or failure scenarios.

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** The main build orchestrator with atomic operations, backup creation, rollback capability, and comprehensive progress tracking. Contains BuildGenerator class with full build lifecycle management.
    *   **Recommendation:** This is the core component being tested. You MUST understand its BuildPhase enum, BuildProgress/BuildResult classes, and all the private methods like `_validate_build_preconditions`, `_create_backup`, `_rollback_from_backup`, etc.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** Markdown processing with python-markdown and pymdown-extensions, frontmatter parsing, content validation, and error handling.
    *   **Recommendation:** Note the MarkdownProcessingError exception class and the comprehensive content validation features. Tests should cover all markdown extensions and validation scenarios.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** Jinja2 template rendering with custom filters, context management, and comprehensive template types (homepage, post, archive, tags, RSS).
    *   **Recommendation:** Pay attention to the custom filters (`dateformat`, `rfc2822`, `excerpt`) and the template validation functionality. Tests should cover all template types and error scenarios.

### Implementation Tips & Notes

*   **Tip:** The existing test suite in `test_build_system.py` already includes most of the required functionality. Look for gaps in coverage rather than rewriting everything. Key areas to potentially expand: edge cases in rollback scenarios, more complex failure combinations, and additional performance tests.

*   **Note:** The task requires ">85% test coverage" - check the existing coverage using the `pytest --cov` command or examine the `htmlcov/` directory to identify specific uncovered lines.

*   **Warning:** The existing tests use extensive mocking which is appropriate for unit tests. For integration tests, the pattern in `test_build_process.py` creates realistic file structures and uses actual components where possible.

*   **Tip:** The BuildGenerator uses phases (BuildPhase enum) for progress tracking. Your tests should verify all phases are executed in the correct order and that failure at any phase triggers proper rollback.

*   **Note:** Performance requirements are strict: <5s for 100 posts. The existing performance tests provide good baselines, but you may need to add more rigorous timing tests with larger content volumes.

*   **Tip:** Atomic operations are critical - tests should verify that builds either complete fully or rollback completely with no partial states left behind.

*   **Note:** The conftest.py file already provides excellent fixtures for configuration testing. You should USE these existing fixtures rather than creating new ones.

### Test Coverage Gaps to Address

Based on the acceptance criteria and existing code review, focus on these areas:

1. **Rollback Integrity:** Test more complex rollback scenarios where backup creation partially fails
2. **Concurrent Safety:** Test what happens if multiple builds run simultaneously
3. **Resource Exhaustion:** Test behavior with very large files or insufficient disk space
4. **Partial Failure Recovery:** Test recovery from interruptions during different build phases
5. **Performance Edge Cases:** Test performance with complex markdown, many tags, large images
6. **Error Propagation:** Ensure all exceptions are properly caught and reported through BuildResult

The task is considered complete when all build components have comprehensive test coverage, atomic operations are verified, rollback scenarios are tested, test coverage exceeds 85%, and performance tests validate the <5s for 100 posts requirement.