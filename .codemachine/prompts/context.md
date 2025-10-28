# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T8",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Create end-to-end tests for complete user workflows including authentication, post creation with images, live preview, publishing, and build processes.",
  "agent_type_hint": "TestingAgent",
  "inputs": "Complete user workflows, E2E testing requirements, HTMX interaction testing",
  "target_files": ["tests/e2e/test_complete_workflows.py", "tests/e2e/test_htmx_interactions.py"],
  "input_files": ["microblog/server/app.py", "microblog/server/routes/api.py", "tests/conftest.py"],
  "deliverables": "End-to-end test suite covering complete user workflows and HTMX functionality",
  "acceptance_criteria": "Complete user journeys tested, HTMX interactions verified, image upload workflows tested, build process integration tested, test coverage comprehensive",
  "dependencies": ["I5.T6", "I5.T7"],
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

### Context: task-i5-t8 (from 02_Iteration_I5.md)

```markdown
    <!-- anchor: task-i5-t8 -->
    *   **Task 5.8:**
        *   **Task ID:** `I5.T8`
        *   **Description:** Create end-to-end tests for complete user workflows including authentication, post creation with images, live preview, publishing, and build processes.
        *   **Agent Type Hint:** `TestingAgent`
        *   **Inputs:** Complete user workflows, E2E testing requirements, HTMX interaction testing
        *   **Input Files:** ["microblog/server/app.py", "microblog/server/routes/api.py", "tests/conftest.py"]
        *   **Target Files:** ["tests/e2e/test_complete_workflows.py", "tests/e2e/test_htmx_interactions.py"]
        *   **Deliverables:** End-to-end test suite covering complete user workflows and HTMX functionality
        *   **Acceptance Criteria:** Complete user journeys tested, HTMX interactions verified, image upload workflows tested, build process integration tested, test coverage comprehensive
        *   **Dependencies:** `I5.T6`, `I5.T7`
        *   **Parallelizable:** Yes
```

### Context: glossary (from 03_Verification_and_Glossary.md)

```markdown
*   **HTMX**: JavaScript library that allows access to AJAX, CSS Transitions, WebSockets and Server-Sent Events directly in HTML using attributes, enabling dynamic interactions without complex JavaScript frameworks.

*   **httpOnly Cookie**: Web cookie with the httpOnly flag set, making it inaccessible to client-side scripts and providing protection against XSS attacks.

*   **JWT (JSON Web Token)**: Compact, URL-safe token format for securely transmitting information between parties as a JSON object, used for stateless authentication.

*   **CSRF (Cross-Site Request Forgery)**: Security vulnerability where unauthorized commands are transmitted from a user that the web application trusts. Prevented using synchronizer tokens.

*   **FastAPI**: Modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints with automatic API documentation.
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `tests/conftest.py`
    *   **Summary:** Contains shared test fixtures including temporary config files, valid/invalid config data, mock authentication callback, and temporary content directory structures. Provides comprehensive fixtures for testing configuration management, authentication flows, and content handling.
    *   **Recommendation:** You MUST leverage the existing fixtures like `valid_config_data`, `temp_config_file`, and `temp_content_dir` for consistent test setup. The mock authentication patterns are already established and should be reused.

*   **File:** `microblog/server/app.py`
    *   **Summary:** Main FastAPI application factory with middleware configuration, route registration, CORS setup, authentication middleware, CSRF protection, and security headers. Includes health check endpoint and startup/shutdown event handlers.
    *   **Recommendation:** You MUST use the `create_app()` function to create test application instances. The app has authentication middleware at `/dashboard`, `/api/`, `/admin/` paths and CSRF protection. Use the health check endpoint `/health` for basic connectivity testing.

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** Complete HTMX API endpoints for dynamic post operations including create, update, delete, publish/unpublish, markdown preview, image upload, build triggering, and tag management. Returns HTML fragments optimized for HTMX integration.
    *   **Recommendation:** You MUST test all HTMX endpoints which return HTML fragments instead of JSON. Key endpoints include `/api/posts` (POST/PUT/DELETE), `/api/preview` (POST), `/api/images/upload` (POST), `/api/build` (POST), and `/api/tags/autocomplete` (GET). All require authentication and CSRF tokens.

*   **File:** `tests/integration/test_dashboard.py`
    *   **Summary:** Comprehensive integration tests for dashboard functionality with sophisticated mocking patterns, template testing, authentication simulation, and complete user workflow testing. Demonstrates proper FastAPI testing with TestClient.
    *   **Recommendation:** You MUST follow the established testing patterns including authentication mocking with `patch('microblog.server.middleware.get_current_user')`, CSRF token mocking, and service mocking. The file shows excellent examples of workflow testing that you should adapt for E2E tests.

### Implementation Tips & Notes
*   **Tip:** The existing integration tests in `test_dashboard.py` show that authentication is mocked using `patch('microblog.server.middleware.get_current_user', return_value=mock_user)`. You SHOULD use the same pattern for E2E tests to ensure consistent authentication simulation.
*   **Note:** The HTMX API endpoints in `api.py` return HTML fragments with specific patterns like error fragments (`_create_error_fragment`) and success fragments (`_create_success_fragment`). Your tests MUST validate these HTML responses and check for HTMX-specific attributes like `hx-swap-oob`.
*   **Warning:** All API endpoints require CSRF tokens for POST/PUT/DELETE operations. The middleware checks for CSRF tokens in headers (`X-CSRF-Token`), form fields (`csrf_token`), or cookies. Your E2E tests MUST include proper CSRF token handling.
*   **Tip:** The application uses both SQLite (for users) and filesystem (for posts/images) storage. The existing `temp_content_dir` fixture creates the proper directory structure including `posts/`, `images/`, `_data/` directories that your tests will need.
*   **Note:** Build operations are asynchronous with job queuing. The `/api/build` endpoint returns job IDs and `/api/build/{job_id}/status` provides progress tracking. Your E2E tests SHOULD test the complete build workflow including status polling.
*   **Warning:** The codebase has extensive error handling with specific exception types like `PostValidationError`, `PostNotFoundError`, `PostFileError`, `ImageValidationError`, and `ImageUploadError`. Your tests MUST verify proper error handling scenarios.
*   **Tip:** Image upload testing requires multipart form data with `enctype="multipart/form-data"`. The existing test patterns show how to handle file uploads with `UploadFile` mocking and validation of the returned markdown snippets.
*   **Note:** The E2E test directory `tests/e2e/` is currently empty, so you're creating the first E2E tests. Follow the naming conventions established in other test directories and use the `Test*` class pattern shown in integration tests.
*   **Warning:** Testing dependencies include `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`, `httpx>=0.25.0`, and `pytest-cov>=4.1.0`. All async operations should be properly handled with `pytest-asyncio` decorators where needed.