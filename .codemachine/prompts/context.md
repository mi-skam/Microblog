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

### Context: security-considerations (from 05_Operational_Architecture.md)

```markdown
**Security Considerations:**

**Input Validation & Sanitization:**
- **Markdown Sanitization**: HTML escaping by default to prevent XSS attacks
- **File Upload Validation**: Extension whitelist, MIME type verification, size limits
- **Path Traversal Prevention**: Filename sanitization and directory boundary enforcement
```

### Context: task-i2-t7 (from 02_Iteration_I2.md)

```markdown
<!-- anchor: task-i2-t7 -->
*   **Task 2.7:**
    *   **Task ID:** `I2.T7`
    *   **Description:** Create comprehensive unit tests for authentication system, user management, and post data models. Ensure security features are thoroughly tested.
    *   **Agent Type Hint:** `TestingAgent`
    *   **Inputs:** Authentication implementation, security requirements, testing best practices
    *   **Input Files:** ["microblog/auth/models.py", "microblog/auth/jwt_handler.py", "microblog/content/post_service.py", "tests/conftest.py"]
    *   **Target Files:** ["tests/unit/test_auth.py", "tests/unit/test_jwt.py", "tests/unit/test_post_service.py"]
    *   **Deliverables:** Comprehensive test suite for authentication and core models
    *   **Acceptance Criteria:** All auth functions tested, JWT generation/validation tested, post operations tested, test coverage >85%, security edge cases covered
    *   **Dependencies:** `I2.T5`, `I2.T4`
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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/auth/models.py`
    *   **Summary:** This file contains the complete User model with SQLite database integration, supporting single-admin-user design. It includes CRUD operations, password hash management, and datetime parsing utilities.
    *   **Recommendation:** You MUST test all class methods including `create_table()`, `create_user()`, `get_by_username()`, `get_by_id()`, `user_exists()`, `update_password()`, and `to_dict()`. Focus on the single-user constraint enforcement and datetime parsing edge cases.

*   **File:** `microblog/auth/jwt_handler.py`
    *   **Summary:** This file provides JWT token creation, validation, and utility functions including token refresh and expiry checking. Uses python-jose library and integrates with configuration system.
    *   **Recommendation:** You MUST test `create_jwt_token()`, `verify_jwt_token()`, `decode_jwt_token_unsafe()`, `get_token_expiry()`, `is_token_expired()`, and `refresh_token()`. Pay special attention to configuration dependencies and error handling.

*   **File:** `microblog/auth/password.py`
    *   **Summary:** This file contains bcrypt password hashing utilities with a minimum cost factor of 12. Includes hashing, verification, and hash analysis functions.
    *   **Recommendation:** You MUST test all password functions for security compliance, Unicode handling, edge cases, and the cost factor requirements. The existing tests provide excellent patterns to follow.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file provides comprehensive post management with markdown/YAML frontmatter, CRUD operations, draft/publish workflow, and filesystem storage. Contains extensive error handling and validation.
    *   **Recommendation:** You MUST test the PostService class thoroughly including `create_post()`, `get_post_by_slug()`, `get_post_by_filename()`, `update_post()`, `delete_post()`, `list_posts()`, and publish/unpublish operations. Test file I/O, validation, and error conditions.

*   **File:** `tests/conftest.py`
    *   **Summary:** This file provides comprehensive test fixtures including temporary files, mock configurations, and test utilities. Offers both valid and invalid config data patterns.
    *   **Recommendation:** You SHOULD leverage existing fixtures like `temp_config_file`, `valid_config_data`, `temp_content_dir`, and `mock_config_callback`. These provide excellent patterns for testing.

### Implementation Tips & Notes

*   **Tip:** I found excellent existing test patterns in `tests/unit/test_auth.py` which already provides comprehensive coverage for User model and password utilities. You SHOULD follow the same testing patterns and structure for consistency.

*   **Note:** The existing JWT tests in `tests/unit/test_jwt.py` demonstrate proper mocking of configuration dependencies using `@patch('microblog.auth.jwt_handler.get_config')`. You MUST use the same pattern for configuration-dependent tests.

*   **Warning:** The task requires >85% test coverage. The existing auth tests show excellent coverage patterns including edge cases, error conditions, and security scenarios. You MUST maintain this level of thoroughness for the post service tests.

*   **Tip:** I confirmed that the project uses pytest with extensive fixtures. The existing test structure shows proper use of temporary databases, file systems, and mock objects. You SHOULD reuse these patterns for consistency.

*   **Security Focus:** The task specifically mentions testing security features. The existing auth tests demonstrate excellent security testing including bcrypt cost factor validation, JWT token security, single-user constraints, and input validation. You MUST apply similar security-focused testing to the post service.

*   **Note:** The PostService uses custom exceptions (`PostNotFoundError`, `PostValidationError`, `PostFileError`). You MUST test these exception scenarios thoroughly as shown in the existing auth test patterns.

*   **Critical:** All target test files (`test_auth.py`, `test_jwt.py`, `test_post_service.py`) already exist. You are UPDATING existing tests, not creating new files. You MUST enhance the existing tests to ensure comprehensive coverage meets the >85% requirement.