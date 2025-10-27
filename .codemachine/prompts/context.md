# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T8",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Create integration tests for dashboard functionality including authentication flows, post management operations, and form submissions. Test complete user workflows.",
  "agent_type_hint": "TestingAgent",
  "inputs": "Dashboard implementation, user workflow requirements, integration testing patterns",
  "target_files": ["tests/integration/test_dashboard.py", "tests/integration/test_auth_flows.py"],
  "input_files": ["microblog/server/app.py", "microblog/server/routes/dashboard.py", "tests/conftest.py"],
  "deliverables": "Integration test suite for dashboard functionality and user workflows",
  "acceptance_criteria": "All dashboard routes tested, authentication flows verified, form submissions tested, user workflows covered, test coverage >80%",
  "dependencies": ["I4.T6", "I4.T7"],
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

### Context: task-i4-t8 (from 02_Iteration_I4.md)

```markdown
    <!-- anchor: task-i4-t8 -->
    *   **Task 4.8:**
        *   **Task ID:** `I4.T8`
        *   **Description:** Create integration tests for dashboard functionality including authentication flows, post management operations, and form submissions. Test complete user workflows.
        *   **Agent Type Hint:** `TestingAgent`
        *   **Inputs:** Dashboard implementation, user workflow requirements, integration testing patterns
        *   **Input Files:** ["microblog/server/app.py", "microblog/server/routes/dashboard.py", "tests/conftest.py"]
        *   **Target Files:** ["tests/integration/test_dashboard.py", "tests/integration/test_auth_flows.py"]
        *   **Deliverables:** Integration test suite for dashboard functionality and user workflows
        *   **Acceptance Criteria:** All dashboard routes tested, authentication flows verified, form submissions tested, user workflows covered, test coverage >80%
        *   **Dependencies:** `I4.T6`, `I4.T7`
        *   **Parallelizable:** Yes
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
├── templates/                      # Jinja2 templates for site generation
│   ├── base.html                   # Base template with common structure
│   ├── index.html                  # Homepage template
│   ├── post.html                   # Individual post template
│   ├── archive.html                # Post listing/archive template
│   ├── tag.html                    # Tag-based post listing
│   ├── rss.xml                     # RSS feed template
│   └── dashboard/                  # Dashboard-specific templates
│       ├── layout.html             # Dashboard base template
│       ├── login.html              # Authentication form
│       ├── posts_list.html         # Post management interface
│       ├── post_edit.html          # Post creation/editing form
│       └── settings.html           # Configuration management
├── static/                         # Static assets for dashboard and site
│   ├── css/
│   │   ├── dashboard.css           # Dashboard-specific styles
│   │   └── site.css                # Public site styles (Pico.css based)
│   ├── js/
│   │   ├── htmx.min.js             # Vendored HTMX library
│   │   └── dashboard.js            # Minimal dashboard JavaScript
│   └── images/
│       └── favicon.ico             # Site favicon
├── docs/                           # Documentation and design artifacts
│   ├── diagrams/                   # UML diagrams (PlantUML source files)
│   │   ├── component_diagram.puml
│   │   ├── database_erd.puml
│   │   ├── auth_flow.puml
│   │   ├── build_process.puml
│   │   └── deployment.puml
│   ├── adr/                        # Architectural Decision Records
│   │   ├── 001-static-first-architecture.md
│   │   ├── 002-single-user-design.md
│   │   └── 003-full-rebuild-strategy.md
│   └── api/                        # API documentation
│       └── openapi.yaml            # OpenAPI v3 specification
├── content/                        # User content directory (runtime)
│   ├── posts/                      # Markdown blog posts
│   ├── pages/                      # Static pages (about, contact, etc.)
│   ├── images/                     # User-uploaded images
│   └── _data/
│       └── config.yaml             # Site configuration
├── build/                          # Generated static site (gitignored)
├── build.bak/                      # Build backup directory (gitignored)
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests for individual components
│   ├── integration/                # Integration tests for API endpoints
│   └── e2e/                        # End-to-end tests for workflows
├── scripts/                        # Deployment and utility scripts
│   ├── deploy.sh                   # Production deployment script
│   ├── backup.sh                   # Content backup script
│   └── dev-setup.sh                # Development environment setup
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container deployment
├── docker-compose.yml              # Local development with Docker
├── .gitignore                      # Git ignore rules
├── README.md                       # Project documentation
└── Makefile                        # Development shortcuts
~~~
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `tests/conftest.py`
    *   **Summary:** This file contains comprehensive shared test fixtures including temporary config files, mock configuration data, content directories, and test utilities. It provides excellent patterns for creating test environments.
    *   **Recommendation:** You MUST reuse the existing fixtures from this file, especially `valid_config_data`, `temp_config_file`, and `temp_content_dir`. The mock callback pattern is also useful for testing configuration reloading.

*   **File:** `microblog/server/app.py`
    *   **Summary:** This file contains the FastAPI application factory with complete middleware setup, route registration, and startup/shutdown event handlers. It includes security headers, CSRF protection, authentication middleware, and development mode configuration.
    *   **Recommendation:** You SHOULD import and use the `create_app()` function from this file for creating test application instances. The application factory pattern is already implemented correctly with dev_mode support.

*   **File:** `microblog/server/routes/dashboard.py`
    *   **Summary:** This file implements all dashboard routes including dashboard home, posts listing, post editing forms, settings, and API endpoints for post creation/updating. It uses proper authentication middleware integration and error handling.
    *   **Recommendation:** You MUST test all the routes defined in this file. Pay special attention to the API endpoints `/api/posts` and `/api/posts/{slug}` which handle form submissions. The error handling patterns and authentication checks should be thoroughly tested.

*   **File:** `tests/integration/test_dashboard.py`
    *   **Summary:** This file already contains extensive integration tests for dashboard functionality including authentication mocking, template creation, post service mocking, and complete workflow testing. It demonstrates excellent testing patterns.
    *   **Recommendation:** You SHOULD examine the existing test patterns carefully. The file shows how to mock authentication, create temporary project directories, set up templates, and test complete workflows. The test structure is well-organized and comprehensive.

*   **File:** `tests/integration/test_auth_flows.py`
    *   **Summary:** This file contains comprehensive authentication flow testing including login/logout workflows, CSRF protection, JWT token handling, session management, and security validation. It demonstrates proper authentication testing patterns.
    *   **Recommendation:** You SHOULD review the authentication testing patterns. The file shows excellent examples of mocking authentication components, testing security features, and validating complete authentication workflows.

### Implementation Tips & Notes

*   **Tip:** I found that both target test files already exist and contain comprehensive test suites. The tests are well-structured and cover the major functionality. However, you should review them for completeness against the acceptance criteria.

*   **Note:** The existing tests use extensive mocking with `unittest.mock.patch` to isolate components and avoid database dependencies. This pattern should be continued for any additional tests you write.

*   **Warning:** The tests require proper environment setup with `MICROBLOG_CONFIG` environment variable and mocked `get_content_dir()` function. Make sure to follow the existing patterns for environment setup to avoid test failures.

*   **Tip:** The test files show excellent examples of testing complete user workflows, including multi-step processes like post creation → editing → publishing. The task requires testing "complete user workflows" so ensure these patterns are comprehensive.

*   **Note:** The existing tests achieve good coverage of authentication flows, dashboard routes, form submissions, and error handling. Pay special attention to CSRF protection testing and authentication requirement validation.

*   **Tip:** The test fixtures in `conftest.py` provide excellent utilities for creating temporary project structures, configuration files, and mock data. These should be reused extensively in your tests.

*   **Note:** Since the acceptance criteria requires ">80% test coverage", you should ensure that any gaps in the existing test coverage are filled. Focus on edge cases, error conditions, and integration points between components.