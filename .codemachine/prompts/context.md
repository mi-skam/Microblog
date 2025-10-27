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

### Context: iteration-3-plan (from 02_Iteration_I3.md)

```markdown
### Iteration 3: Static Site Generation & Build System

*   **Iteration ID:** `I3`
*   **Goal:** Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback
*   **Prerequisites:** `I2` (Authentication and core models completed)
*   **Tasks:**

    *   **Task 3.7:**
        *   **Task ID:** `I3.T7`
        *   **Description:** Create comprehensive tests for build system including markdown processing, template rendering, asset management, and atomic build operations. Test build failure and rollback scenarios.
        *   **Agent Type Hint:** `TestingAgent`
        *   **Inputs:** Build system implementation, testing requirements, failure scenario testing
        *   **Input Files:** ["microblog/builder/generator.py", "microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "tests/conftest.py"]
        *   **Target Files:** ["tests/unit/test_build_system.py", "tests/integration/test_build_process.py"]
        *   **Deliverables:** Comprehensive build system test suite with failure scenario testing
        *   **Acceptance Criteria:** All build components tested, atomic operations verified, rollback scenarios tested, test coverage >85%, performance tests included
        *   **Dependencies:** `I3.T5`, `I3.T6`
        *   **Parallelizable:** Yes
```

### Context: verification-and-integration-strategy (from 03_Verification_and_Glossary.md)

```markdown
## 5. Verification and Integration Strategy

*   **Testing Levels:**
    *   **Unit Testing**: Individual component testing with pytest, focusing on business logic, authentication, content processing, and build system components. Target coverage >85% for all modules with comprehensive edge case testing.
    *   **Integration Testing**: API endpoint testing, database interactions, file system operations, and service integration testing. Verify authentication flows, content management workflows, and build system integration.
    *   **End-to-End Testing**: Complete user workflow testing including authentication, post creation, editing, publishing, and build processes. Test HTMX interactions, form submissions, and dashboard functionality.
    *   **Performance Testing**: Build time validation (<5s for 100 posts, <30s for 1000 posts), API response time verification (<200ms), and load testing for concurrent dashboard users.
    *   **Security Testing**: Authentication security, CSRF protection, input validation, file upload security, and SQL injection prevention testing.

*   **CI/CD:**
    *   **Automated Testing**: All tests run on every commit with GitHub Actions or similar CI system
    *   **Code Quality Gates**: Ruff linting, type checking with mypy, security scanning with bandit
    *   **Build Validation**: Automated build testing with sample content, template rendering verification
    *   **Artifact Validation**: OpenAPI specification validation, PlantUML diagram syntax checking, configuration schema validation
    *   **Deployment Testing**: Docker image building, deployment script validation, service configuration testing

*   **Code Quality Gates:**
    *   **Linting Success**: All code must pass Ruff linting with zero errors and warnings
    *   **Type Coverage**: Minimum 90% type hint coverage with mypy validation
    *   **Test Coverage**: Minimum 85% code coverage across all modules
    *   **Security Scan**: Zero high-severity security vulnerabilities detected by bandit
    *   **Performance Benchmarks**: All performance targets met in automated testing
    *   **Documentation Coverage**: All public APIs and configuration options documented
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

**Rationale for Architectural Choice:**

- **Performance**: Static files provide sub-100ms page loads and can handle high traffic without server resources
- **Simplicity**: Monolithic dashboard avoids distributed system complexity while maintaining clear internal boundaries
- **Deployment Flexibility**: Static output can be deployed anywhere (CDN, static hosts, traditional servers)
- **Developer Experience**: Clear separation enables focused development on each concern without cross-cutting complexity
- **Reliability**: Atomic builds with rollback capabilities ensure consistent site state
- **Security**: Static content eliminates many attack vectors; dynamic interface has minimal surface area
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** This is the main build orchestrator implementing atomic build operations with backup/rollback capabilities. It coordinates markdown processing, template rendering, and asset copying with comprehensive progress tracking and error handling.
    *   **Recommendation:** You MUST test all phases of the BuildGenerator.build() method including BuildPhase enumeration, BuildProgress reporting, BuildResult return values, and all failure scenarios with rollback mechanisms.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** Markdown processor with python-markdown and pymdown-extensions for content processing. Includes frontmatter parsing, syntax highlighting, and content validation.
    *   **Recommendation:** You SHOULD test the MarkdownProcessor class including process_content(), process_markdown_text(), validate_and_process(), and validate_content_structure() methods. Test both valid and invalid markdown content.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** Jinja2 template rendering engine with site-wide context management, custom filters, and RSS feed generation. Handles template inheritance and validation.
    *   **Recommendation:** You MUST test the TemplateRenderer class including all rendering methods (render_homepage, render_post, render_archive, render_tag_page, render_rss_feed) and template validation functionality.

*   **File:** `microblog/builder/asset_manager.py`
    *   **Summary:** Asset management system for copying images and static files with validation, security checks, and change detection. Implements file validation and copying with error handling.
    *   **Recommendation:** You SHOULD test the AssetManager class including copy_all_assets(), validate_file(), copy_directory_assets(), and security validation features.

*   **File:** `tests/conftest.py`
    *   **Summary:** Contains shared pytest fixtures for configuration data, temporary files, and test utilities used across the test suite.
    *   **Recommendation:** You MUST use the existing fixtures (temp_content_dir, valid_config_data, temp_config_file) and create additional fixtures for build system testing including mock content and templates.

### Implementation Tips & Notes

*   **Tip:** The build system implements atomic operations with backup/rollback functionality. Your tests MUST verify that builds either complete successfully or rollback completely without leaving partial state.

*   **Note:** BuildGenerator uses BuildPhase enum for progress tracking. Test all phases: INITIALIZING, BACKUP_CREATION, CONTENT_PROCESSING, TEMPLATE_RENDERING, ASSET_COPYING, VERIFICATION, CLEANUP, ROLLBACK, COMPLETED, FAILED.

*   **Warning:** The project requires >85% test coverage. Ensure you test all major code paths including success scenarios, various failure modes, and edge cases like empty content, missing templates, and invalid files.

*   **Tip:** Performance testing is required with build time targets: <5s for 100 posts, <30s for 1000 posts. Create performance tests that validate these requirements.

*   **Note:** The existing test structure follows pytest patterns with unit tests in tests/unit/ and integration tests in tests/integration/. Follow this pattern and use descriptive test method names like test_build_success_with_valid_content().

*   **Warning:** Rollback scenarios are critical for atomic build safety. Test failure modes like template errors, markdown processing failures, asset copying failures, and verify that rollback restores the previous build state.

*   **Tip:** The build system processes different content types (markdown posts, templates, assets). Create comprehensive test data for each type and test the complete pipeline from source to generated output.