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

### Context: task-i3-t7 (from 02_Iteration_I3.md)

```markdown
    <!-- anchor: task-i3-t7 -->
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
*   **Testing Levels:**
    *   **Unit Testing**: Individual component testing with pytest, focusing on business logic, authentication, content processing, and build system components. Target coverage >85% for all modules with comprehensive edge case testing.
    *   **Integration Testing**: API endpoint testing, database interactions, file system operations, and service integration testing. Verify authentication flows, content management workflows, and build system integration.
    *   **Performance Testing**: Build time validation (<5s for 100 posts, <30s for 1000 posts), API response time verification (<200ms), and load testing for concurrent dashboard users.

*   **Code Quality Gates:**
    *   **Test Coverage**: Minimum 85% code coverage across all modules
    *   **Performance Benchmarks**: All performance targets met in automated testing
```

### Context: reliability-availability (from 05_Operational_Architecture.md)

```markdown
**Fault Tolerance:**
- **Atomic Builds**: Complete success or complete rollback for site generation
- **Backup Strategy**: Automatic backup creation before each build operation
- **Rollback Capability**: Instant restoration to previous working state on build failure
- **Error Recovery**: Graceful handling of file system and permission errors

**High Availability Design:**
def atomic_build():
    backup_current_build()  # Preserve working state
    try:
        generate_new_build()  # Create complete new build
        validate_build_output()  # Verify build integrity
        activate_new_build()  # Atomic swap to new version
    except Exception as e:
        restore_from_backup()  # Rollback on any failure
        raise BuildFailedException(f"Build failed: {e}")
    finally:
        cleanup_old_backups()  # Maintain backup retention
```

### Context: scalability-performance (from 05_Operational_Architecture.md)

```markdown
**Build Performance:**
BUILD_PERFORMANCE_TARGETS = {
    "100_posts": "< 5 seconds",
    "1000_posts": "< 30 seconds",
    "markdown_parsing": "< 100ms per file",
    "template_rendering": "< 50ms per page",
    "image_copying": "< 1GB per minute"
}

**Performance Monitoring:**
- **Build Time Tracking**: Monitoring build duration and identifying bottlenecks
- **API Response Times**: Dashboard endpoint performance measurement
- **Resource Usage**: Memory and CPU utilization during build processes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `tests/unit/test_build_system.py`
    *   **Summary:** This file already contains extensive unit tests for the build system components including markdown processing, template rendering, asset management, and build generator functionality.
    *   **Recommendation:** You MUST build upon the existing comprehensive test structure. The file contains 1,516 lines of well-structured tests that you should extend, not replace.

*   **File:** `tests/integration/test_build_process.py`
    *   **Summary:** This file contains integration tests for the complete build process with realistic project structures and end-to-end workflows.
    *   **Recommendation:** You SHOULD extend this file with additional failure scenarios and rollback testing as it already has a solid foundation for integration testing.

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** The main build generator implementing atomic operations with comprehensive error handling, progress tracking, and rollback mechanisms. Contains BuildPhase enum, BuildProgress/BuildResult classes, and BuildGenerator with full lifecycle management.
    *   **Recommendation:** You MUST use the existing BuildPhase enum values and BuildResult structure in your tests. The atomic build process includes backup creation, content processing, template rendering, asset copying, verification, and cleanup phases.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** Markdown processor with python-markdown and pymdown-extensions, supporting YAML frontmatter parsing, syntax highlighting, and content validation.
    *   **Recommendation:** You SHOULD test the MarkdownProcessingError exception handling and the validate_content_structure method for edge cases.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** Jinja2 template rendering system with template inheritance, custom filters, and context management for homepage, posts, archive, tags, and RSS feed generation.
    *   **Recommendation:** You MUST test the TemplateRenderingError exception handling and custom template filters (_format_date, _create_excerpt, _format_rfc2822).

*   **File:** `microblog/builder/asset_manager.py`
    *   **Summary:** Asset manager with file validation, security checks, path management, and change detection. Includes allowed file extensions, file size limits, and suspicious file pattern detection.
    *   **Recommendation:** You SHOULD test the AssetManagingError exception handling and security validation features including large file rejection and suspicious file detection.

*   **File:** `tests/conftest.py`
    *   **Summary:** Shared test fixtures providing temporary files, mock configurations, and test utilities used across all test modules.
    *   **Recommendation:** You MUST import and use the existing fixtures (valid_config_data, temp_content_dir, mock_config_callback) for consistency.

### Implementation Tips & Notes
*   **Tip:** The existing test structure is already comprehensive with 1,516 lines covering unit tests for all components. Focus on extending failure scenarios and rollback testing rather than duplicating existing coverage.
*   **Note:** The build system uses atomic operations with backup/rollback mechanisms. Your failure scenario tests should verify that BuildPhase.ROLLBACK and BuildPhase.FAILED phases are properly triggered and that backup restoration works correctly.
*   **Warning:** The existing tests use extensive mocking with unittest.mock. Ensure your new tests follow the same mocking patterns and don't interfere with the existing global instance management (get_markdown_processor, get_template_renderer, etc.).
*   **Performance Requirement:** The acceptance criteria requires build time validation (<5s for 100 posts). The existing tests include performance tests in TestPerformanceBuildTests class - extend these rather than creating new ones.
*   **Coverage Target:** You need >85% test coverage. The existing tests are comprehensive, so focus on edge cases and error scenarios that might not be covered yet.
*   **Rollback Testing:** The existing tests include some rollback scenarios in TestBuildFailureScenarios class. Extend this class with additional atomic operation failure tests and verify backup integrity.
*   **Integration Focus:** The integration tests already cover realistic project structures. Add tests for corrupted templates, large file handling, permission issues, and concurrent build scenarios.
*   **Testing Strategy:** Use pytest fixtures from conftest.py, mock external dependencies, test both success and failure paths, and verify progress tracking and error reporting work correctly.