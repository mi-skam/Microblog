# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T7",
  "iteration_id": "I2",
  "iteration_goal": "Implement authentication system with JWT tokens, user management, and core data models for posts and images",
  "description": "Create comprehensive unit tests for authentication system, user management, and post data models. Ensure security features are thoroughly tested.",
  "agent_type_hint": "TestingAgent",
  "inputs": "Authentication implementation, security requirements, testing best practices",
  "target_files": ["tests/unit/test_auth.py", "tests/unit/test_jwt.py", "tests/unit/test_post_service.py"],
  "input_files": ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "microblog/content/post_service.py", "tests/conftest.py"],
  "deliverables": "Comprehensive test suite for authentication and core models",
  "acceptance_criteria": "All auth functions tested, JWT generation/validation tested, post operations tested, test coverage >85%, security edge cases covered",
  "dependencies": ["I2.T5", "I2.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: authentication-authorization (from 05_Operational_Architecture.md)

```markdown
**Authentication & Authorization:**

**Authentication Strategy:**
- **Single-User Design**: System supports exactly one admin user with fixed role
- **JWT-Based Sessions**: Stateless authentication using JSON Web Tokens
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

### Context: task-i2-t3 (from 02_Iteration_I2.md)

```markdown
*   **Task 2.3:**
    *   **Task ID:** `I2.T3`
    *   **Description:** Implement User model with SQLite database, bcrypt password hashing, and JWT token management. Create database schema and user creation utilities.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** User model specification, security requirements (bcrypt cost ≥12), JWT configuration
    *   **Input Files:** ["microblog/server/config.py", "docs/diagrams/database_erd.puml"]
    *   **Target Files:** ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "microblog/auth/password.py", "microblog/database.py"]
    *   **Deliverables:** User SQLite model, password hashing utilities, JWT token generation/validation, database initialization
    *   **Acceptance Criteria:** User creation works correctly, passwords hash with bcrypt cost ≥12, JWT tokens generate and validate properly, database initializes automatically
    *   **Dependencies:** `I1.T4`
    *   **Parallelizable:** No
```

### Context: task-i2-t4 (from 02_Iteration_I2.md)

```markdown
*   **Task 2.4:**
    *   **Task ID:** `I2.T4`
    *   **Description:** Create Post data model for markdown file handling with YAML frontmatter parsing, validation, and filesystem operations. Implement draft/published status management.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Post model specification, markdown processing requirements, file system storage strategy
    *   **Input Files:** ["microblog/server/config.py", "docs/diagrams/database_erd.puml"]
    *   **Target Files:** ["microblog/content/post_service.py", "microblog/content/validators.py"]
    *   **Deliverables:** Post service with CRUD operations, frontmatter validation, markdown file handling, draft/publish workflow
    *   **Acceptance Criteria:** Posts save/load from markdown files correctly, YAML frontmatter parses properly, validation catches invalid data, draft/publish status works
    *   **Dependencies:** `I1.T4`
    *   **Parallelizable:** Yes
```

### Context: task-i2-t5 (from 02_Iteration_I2.md)

```markdown
*   **Task 2.5:**
    *   **Task ID:** `I2.T5`
    *   **Description:** Implement authentication middleware, CSRF protection, and session management for FastAPI application. Create login/logout endpoints with secure cookie handling.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Authentication flow from diagrams, security requirements, FastAPI middleware patterns
    *   **Input Files:** ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "docs/diagrams/auth_flow.puml"]
    *   **Target Files:** ["microblog/server/middleware.py", "microblog/server/routes/auth.py"]
    *   **Deliverables:** Authentication middleware, CSRF protection, login/logout endpoints, secure session management
    *   **Acceptance Criteria:** Middleware validates JWT tokens correctly, CSRF tokens prevent attacks, login sets httpOnly cookies, logout clears sessions properly
    *   **Dependencies:** `I2.T3`
    *   **Parallelizable:** No
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/auth/models.py`
    *   **Summary:** Contains the User SQLite model with complete CRUD operations, single-user constraint, and datetime parsing utilities. Includes table creation, user lookup by username/ID, and password update functionality.
    *   **Recommendation:** You MUST test all User model methods including create_user, get_by_username, get_by_id, user_exists, and update_password. Pay special attention to the single-user constraint validation and datetime parsing edge cases.

*   **File:** `microblog/auth/jwt_handler.py`
    *   **Summary:** Complete JWT token management with create_jwt_token, verify_jwt_token, and utility functions for token inspection and refresh. Uses jose library and integrates with config system.
    *   **Recommendation:** You MUST test JWT creation with valid/invalid configs, token verification with expired/malformed tokens, and all utility functions. Test the integration with the configuration system.

*   **File:** `microblog/auth/password.py`
    *   **Summary:** Bcrypt password hashing utilities with fixed cost factor 12, password verification, and hash analysis functions. Includes security validation for hash strength.
    *   **Recommendation:** You MUST test password hashing with various inputs including edge cases (empty strings, unicode), hash verification, and the needs_update functionality for cost factor validation.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** Comprehensive post management service with CRUD operations, frontmatter parsing, file system operations, and draft/publish workflow. Contains extensive error handling and validation.
    *   **Recommendation:** You MUST test all PostService methods including create_post, get_post_by_slug, update_post, delete_post, list_posts, and publish/unpublish operations. Focus on filesystem error handling and validation edge cases.

*   **File:** `microblog/server/middleware.py`
    *   **Summary:** Complete authentication and CSRF middleware implementations with JWT cookie handling, route protection, and security headers. Includes helper functions for user and CSRF token management.
    *   **Recommendation:** You SHOULD test the middleware components, especially the authentication flow and CSRF protection mechanisms, as they are critical security features.

*   **File:** `tests/conftest.py`
    *   **Summary:** Well-established test fixtures including temp files, valid/invalid config data, and mock utilities. Provides comprehensive testing infrastructure.
    *   **Recommendation:** You SHOULD leverage existing fixtures like valid_config_data, temp_config_file, and temp_content_dir. Consider adding database and authentication-specific fixtures.

### Implementation Tips & Notes
*   **Tip:** The project uses pytest with extensive fixtures already available in conftest.py. You SHOULD reuse the existing config fixtures and patterns for consistency.
*   **Note:** The User model implements a single-user constraint that raises ValueError when attempting to create multiple users. Your tests MUST verify this constraint works correctly.
*   **Warning:** JWT tokens depend on configuration (jwt_secret, session_expires). Your tests MUST mock or provide valid configuration data to test JWT functionality properly.
*   **Tip:** The post service uses filesystem operations with comprehensive error handling. You SHOULD test both success and failure scenarios, including file permission issues and malformed YAML.
*   **Note:** Password hashing uses bcrypt with cost factor 12. Your tests SHOULD verify the minimum cost requirement and test the needs_update functionality.
*   **Tip:** The project already has a .coverage file indicating coverage tracking is active. Aim for >85% coverage as specified in the acceptance criteria.
*   **Warning:** Some modules like post_service have complex interdependencies with the config system and file operations. You MUST use proper mocking or temporary directories to isolate tests.
*   **Note:** The authentication system integrates multiple components (User model, JWT handler, password utilities). Consider testing the complete authentication flow as well as individual components.