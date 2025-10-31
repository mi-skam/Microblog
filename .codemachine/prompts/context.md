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

### Context: authentication-authorization (from 05_Operational_Architecture.md)

```markdown
**Authentication & Authorization:**

**Single-User JWT-Based Authentication:**
- **User Credentials**: Username/password stored with bcrypt hash (cost ≥12)
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Secure Token Storage**: JWT stored in httpOnly, Secure, SameSite=Strict cookies
- **Password Security**: Bcrypt hashing with cost factor ≥12 for password storage
- **Session Management**: Configurable token expiration (default 2 hours)

**Implementation Details:**
```python
# Authentication flow
def authenticate_user(username: str, password: str) -> Optional[User]:
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        token = create_jwt_token(user.user_id, user.username)
        return user, token
    return None

# JWT Token Structure
{
    "user_id": 1,
    "username": "admin",
    "role": "admin",
    "exp": 1635724800,  # Expiration timestamp
    "iat": 1635721200   # Issued at timestamp
}
```

**Authorization Model:**
- **Role-Based**: Single admin role with full system access
- **Route Protection**: Middleware validates JWT for protected endpoints
- **CSRF Protection**: All state-changing operations require valid CSRF tokens
- **Session Validation**: Automatic token expiration and renewal handling
```

### Context: htmx-integration (from 04_Behavior_and_Communication.md)

```markdown
**HTMX Integration Patterns:**

1. **Live Form Validation**
```html
<input name="title"
       hx-post="/api/validate/title"
       hx-trigger="blur"
       hx-target="#title-feedback">
```

2. **Dynamic Content Updates**
```html
<button hx-delete="/api/posts/123"
        hx-confirm="Delete this post?"
        hx-target="#post-123"
        hx-swap="outerHTML">Delete</button>
```

3. **Live Markdown Preview**
```html
<textarea name="content"
          hx-post="/api/preview"
          hx-trigger="keyup changed delay:500ms"
          hx-target="#preview-pane">
```

4. **Build Progress Updates**
```html
<button hx-post="/api/build"
        hx-target="#build-status"
        hx-indicator="#build-spinner">Rebuild Site</button>
```
```

### Context: api-endpoints-detail (from 04_Behavior_and_Communication.md)

```markdown
**Image Upload Endpoint:**
```
POST /api/images
Headers: Cookie: jwt=...; X-CSRF-Token: ...
Content-Type: multipart/form-data
Body: file=@image.jpg
Response: 201 Created + JSON with image URL and markdown snippet
{
  "filename": "2025-10-26-image.jpg",
  "url": "../images/2025-10-26-image.jpg",
  "markdown": "![Image description](../images/2025-10-26-image.jpg)"
}
```
```

### Context: key-interaction-flow (from 04_Behavior_and_Communication.md)

```markdown
== Authentication Flow ==
author -> browser : Enter credentials and login
browser -> dashboard : POST /auth/login (username, password)
dashboard -> auth : Validate credentials
auth -> dashboard : JWT token
dashboard -> browser : Set httpOnly cookie + redirect
browser -> author : Show dashboard interface

== Post Creation Flow ==
author -> browser : Click "New Post"
browser -> dashboard : GET /dashboard/posts/new
dashboard -> browser : HTML form with CSRF token
author -> browser : Fill form (title, content, tags)
browser -> dashboard : POST /api/posts (HTMX request)

dashboard -> auth : Validate JWT from cookie
auth -> dashboard : User authenticated

dashboard -> posts : Create post with metadata
posts -> storage : Write markdown file
storage -> posts : File created successfully
posts -> dashboard : Post created

dashboard -> generator : Trigger build process
generator -> storage : Read all content files
storage -> generator : Content data
generator -> build : Generate static HTML
build -> generator : Build completed
generator -> dashboard : Build status

dashboard -> browser : HTML fragment with success message
browser -> author : Show updated post list + success

== Live Preview Flow ==
author -> browser : Type in markdown editor
note right : 500ms debounce
browser -> dashboard : POST /api/preview (HTMX)
dashboard -> posts : Render markdown
posts -> dashboard : HTML preview
dashboard -> browser : HTML fragment
browser -> author : Live preview updated
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `tests/conftest.py`
    *   **Summary:** This file contains comprehensive test fixtures including temporary config files, valid/invalid config data, mock callbacks, and content directory setup.
    *   **Recommendation:** You MUST import and use the existing fixtures from this file, especially `temp_content_dir`, `valid_config_data`, and authentication-related mocks.

*   **File:** `tests/e2e/test_complete_workflows.py`
    *   **Summary:** This file contains the current E2E test implementation with authentication mocks, temporary project directory setup, and comprehensive workflow tests.
    *   **Recommendation:** You SHOULD build upon the existing test patterns in this file. The authentication mocking strategy using middleware dispatch functions is already established and working.

*   **File:** `tests/e2e/test_htmx_interactions.py`
    *   **Summary:** This file contains HTMX-specific testing with comprehensive API endpoint testing, fragment validation, and service mocking patterns.
    *   **Recommendation:** You MUST follow the existing HTMX testing patterns, particularly the fragment validation and service mocking approaches.

*   **File:** `microblog/server/app.py`
    *   **Summary:** This file contains the FastAPI application factory with middleware configuration, route registration, and authentication setup.
    *   **Recommendation:** You SHOULD use the `create_app()` function for testing and understand the middleware layering order: SecurityHeaders -> CSRF -> Authentication.

*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file contains HTMX API endpoints that return HTML fragments for dynamic operations including post CRUD, preview, image upload, and build operations.
    *   **Recommendation:** You MUST test the HTML fragment responses and ensure they contain the proper HTMX attributes like `hx-swap-oob` and alert classes.

### Implementation Tips & Notes
*   **Tip:** The existing E2E tests already have a comprehensive authentication mocking strategy using `patch` to mock middleware dispatch functions. You SHOULD reuse this pattern for consistent authentication handling.
*   **Note:** The tests use `TestClient` from FastAPI for HTTP requests and heavily mock the service layer. This approach isolates testing from actual file system operations.
*   **Tip:** HTMX interactions are tested by verifying HTML fragment content, response headers (`text/html`), and specific CSS classes like `alert-success`, `alert-error`, and `hx-swap-oob`.
*   **Note:** The current tests follow a pattern of creating mock services and patching them using `with patch()` context managers. Continue this pattern for consistency.
*   **Warning:** The existing tests use temporary directories and mock configurations to avoid interfering with actual project files. You MUST maintain this isolation in any new tests.
*   **Tip:** Image upload testing uses `BytesIO` objects to simulate file uploads without requiring actual image files.
*   **Note:** Build process testing mocks the build service and job status objects to simulate different build states (queued, running, completed, failed).
*   **Tip:** The tests validate both successful workflows and error handling scenarios. You SHOULD ensure comprehensive error path testing in your implementation.
*   **Warning:** Authentication middleware can interfere with testing, so the existing tests have comprehensive mocking strategies to bypass authentication while still testing the workflow logic.

### Key Testing Patterns Established
*   **Authentication Mocking:** Use middleware dispatch function mocking to simulate authenticated users
*   **Service Mocking:** Mock all service layer dependencies using `unittest.mock.patch`
*   **HTML Fragment Validation:** Verify HTMX responses contain proper structure, classes, and content
*   **Error Scenario Testing:** Test validation errors, service failures, and edge cases
*   **Temporary Isolation:** Use temporary directories and mock configurations to avoid side effects

### Critical Task Implementation Notes
*   **IMPORTANT:** The target files already exist and contain substantial test implementations. You are NOT creating new files from scratch, but rather ENHANCING and EXPANDING the existing tests.
*   **IMPORTANT:** Both `test_complete_workflows.py` and `test_htmx_interactions.py` already have comprehensive test coverage. Your task is to ADD new test methods that cover missing scenarios from the acceptance criteria.
*   **MISSING COVERAGE AREAS to address:**
    1. **Image upload workflows** in complete user journeys
    2. **Build process integration** testing in end-to-end scenarios
    3. **Live preview functionality** in complete workflows
    4. **Cross-feature integration** testing (e.g., post creation -> image upload -> live preview -> publish -> build)
    5. **Performance validation** for user workflows
    6. **Accessibility testing** for HTMX interactions

### Specific Implementation Guidance
*   **For `test_complete_workflows.py`:** Add test methods that combine multiple features in realistic user journeys (e.g., create post with image, preview, edit, publish, trigger build)
*   **For `test_htmx_interactions.py`:** Add comprehensive testing for any HTMX endpoints not fully covered, especially complex interaction patterns
*   **Use existing patterns:** Both files have well-established mocking and testing patterns - maintain consistency with these approaches
*   **Error coverage:** Ensure error scenarios are tested for all new workflow combinations