# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T5",
  "iteration_id": "I1",
  "iteration_goal": "Establish project foundation, directory structure, core architecture documentation, and basic CLI framework",
  "description": "Set up basic testing framework with pytest, create test directory structure, and implement initial unit tests for configuration management. Establish testing patterns and CI-ready test execution.",
  "agent_type_hint": "TestingAgent",
  "inputs": "Testing requirements, code quality standards, pytest best practices",
  "target_files": ["tests/unit/test_config.py", "tests/conftest.py", "pytest.ini"],
  "input_files": ["pyproject.toml", "microblog/server/config.py"],
  "deliverables": "Pytest configuration, test utilities, configuration manager tests, test execution scripts",
  "acceptance_criteria": "Tests run successfully with `pytest`, configuration loading and validation tested, test coverage >80% for config module, CI-ready test execution",
  "dependencies": ["I1.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

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

*   **Artifact Validation:**
    *   **PlantUML Diagrams**: Syntax validation and rendering verification for all diagram files
    *   **OpenAPI Specification**: Schema validation and endpoint coverage verification
    *   **Configuration Schema**: JSON Schema validation and comprehensive setting coverage
    *   **Documentation Quality**: Spelling, grammar, and link validation for all documentation
    *   **Template Validation**: Jinja2 template syntax checking and rendering verification
    *   **Build Output Validation**: Generated HTML validation, link checking, and asset verification
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
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests for individual components
│   ├── integration/                # Integration tests for API endpoints
│   └── e2e/                        # End-to-end tests for workflows
~~~
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `pyproject.toml`
    *   **Summary:** This file contains the complete Python project configuration including pytest settings, test dependencies, and coverage configuration. The pytest configuration is already set up with test paths, coverage settings, and proper addopts.
    *   **Recommendation:** You MUST use the existing pytest configuration which includes coverage reporting (`--cov=microblog --cov-report=term-missing`). The dev dependencies already include all needed testing packages: pytest>=7.4.0, pytest-asyncio>=0.21.0, httpx>=0.25.0, pytest-cov>=4.1.0.
*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains a comprehensive configuration management system with Pydantic models (AppConfig, SiteConfig, BuildConfig, ServerConfig, AuthConfig), YAML loading, validation, and hot-reload capabilities using file watchers.
    *   **Recommendation:** You MUST write unit tests for the ConfigManager class and all its key methods including load_config(), reload_config(), validate_config_file(), and the Pydantic model validation. Focus on testing error conditions like missing files, invalid YAML, and validation failures.
*   **File:** `microblog/utils.py`
    *   **Summary:** This file provides shared utility functions for directory management, file operations, and path resolution including ensure_directory(), safe_copy_file(), and various get_*_dir() functions.
    *   **Recommendation:** You SHOULD import and use the utility functions from this file in your tests, especially get_content_dir() for locating test configuration files and ensure_directory() for test setup.
*   **File:** `content/_data/config.yaml`
    *   **Summary:** This file contains the default configuration structure with all required sections (site, build, server, auth) and demonstrates the expected YAML format.
    *   **Recommendation:** You SHOULD use this file as a reference for creating test configuration fixtures and testing valid configuration loading scenarios.

### Implementation Tips & Notes
*   **Tip:** The project already has a complete pytest configuration in pyproject.toml with coverage settings. You do NOT need to create a separate pytest.ini file unless you need to override specific settings.
*   **Note:** The ConfigManager class uses asyncio for file watching and has comprehensive error handling. Your tests MUST include async testing scenarios using pytest-asyncio for the hot-reload functionality.
*   **Warning:** The configuration validation is strict and uses Pydantic models. Your tests MUST cover edge cases like empty files, malformed YAML, missing required fields, and validation constraint violations (e.g., JWT secret length requirements).
*   **Tip:** The existing test directory structure follows pytest conventions with separate unit/, integration/, and e2e/ directories. Place your configuration tests in tests/unit/test_config.py as specified in the target_files.
*   **Note:** The target coverage requirement is >80% for the config module specifically, and the overall project targets >85% coverage. Focus on testing all public methods and error paths in the ConfigManager class.
*   **Tip:** Create a tests/conftest.py file for shared test fixtures, particularly for creating temporary configuration files and mock configuration data that can be reused across different test modules.