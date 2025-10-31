# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I6.T2",
  "iteration_id": "I6",
  "iteration_goal": "Implement production features, security hardening, deployment support, comprehensive documentation, and final system testing",
  "description": "Implement security hardening including rate limiting on authentication, security headers, input sanitization, and vulnerability protection. Add security audit logging.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Security requirements, rate limiting patterns, vulnerability protection",
  "target_files": ["microblog/server/security.py", "microblog/server/middleware.py"],
  "input_files": ["microblog/server/middleware.py", "microblog/server/routes/auth.py"],
  "deliverables": "Rate limiting implementation, security headers, input sanitization, vulnerability protection, security audit logging",
  "acceptance_criteria": "Rate limiting prevents brute force attacks, security headers set correctly, input sanitization prevents XSS, audit logs capture security events",
  "dependencies": ["I4.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: security-considerations (from 05_Operational_Architecture.md)

```markdown
**Security Considerations:**

**Input Validation & Sanitization:**
- **Markdown Sanitization**: HTML escaping by default to prevent XSS attacks
- **File Upload Validation**: Extension whitelist, MIME type verification, size limits
- **Path Traversal Prevention**: Filename sanitization and directory boundary enforcement
- **SQL Injection Prevention**: Parameterized queries for all database operations
- **Command Injection Prevention**: No direct shell execution from user input

**Security Headers:**
```python
# Security middleware configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'"
}
```

**Data Protection:**
- **Secrets Management**: JWT secret stored in configuration with minimum 32-character requirement
- **Database Security**: SQLite file permissions restricted to application user
- **File System Security**: Content directory permissions preventing unauthorized access
- **Backup Security**: Build backups stored with same security constraints as primary data

**Vulnerability Mitigation:**
- **Rate Limiting**: Authentication endpoint protection against brute force attacks
- **CSRF Protection**: Synchronizer token pattern for all state-changing operations
- **Session Security**: Automatic token expiration and secure cookie attributes
- **Dependency Scanning**: Regular security updates for Python dependencies
```

### Context: logging-monitoring (from 05_Operational_Architecture.md)

```markdown
**Logging & Monitoring:**

**Logging Strategy:**
- **Structured Logging**: JSON-formatted logs for machine processing
- **Log Levels**: DEBUG (dev), INFO (operations), WARN (issues), ERROR (failures)
- **Security Logging**: Failed authentication attempts, CSRF violations
- **Performance Logging**: Build times, API response times, file operations
- **Audit Logging**: Content modifications, user actions, configuration changes

**Log Configuration:**
```python
# Logging setup
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "structured": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "microblog.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    }
}
```

**Monitoring Capabilities:**
- **Health Checks**: API endpoint for system status verification
- **Build Monitoring**: Track build success/failure rates and durations
- **File System Monitoring**: Disk space usage and permission issues
- **Performance Metrics**: Response times, concurrent users, resource usage
- **Error Tracking**: Automatic error aggregation and alerting
```

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

### Context: task-i6-t2 (from 02_Iteration_I6.md)

```markdown
<!-- anchor: task-i6-t2 -->
*   **Task 6.2:**
    *   **Task ID:** `I6.T2`
    *   **Description:** Implement security hardening including rate limiting on authentication, security headers, input sanitization, and vulnerability protection. Add security audit logging.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Security requirements, rate limiting patterns, vulnerability protection
    *   **Input Files:** ["microblog/server/middleware.py", "microblog/server/routes/auth.py"]
    *   **Target Files:** ["microblog/server/security.py", "microblog/server/middleware.py"]
    *   **Deliverables:** Rate limiting implementation, security headers, input sanitization, vulnerability protection, security audit logging
    *   **Acceptance Criteria:** Rate limiting prevents brute force attacks, security headers set correctly, input sanitization prevents XSS, audit logs capture security events
    *   **Dependencies:** `I4.T4`
    *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/middleware.py`
    *   **Summary:** This file contains comprehensive authentication middleware (JWT validation), CSRF protection middleware, and basic security headers middleware. It already implements secure session management with proper cookie handling.
    *   **Recommendation:** You MUST extend the existing `SecurityHeadersMiddleware` class to include the additional security headers specified in the architecture. The current implementation has basic headers but needs the full HSTS and CSP headers from the spec.

*   **File:** `microblog/server/routes/auth.py`
    *   **Summary:** This file contains all authentication routes including login, logout, and session checking. It properly validates CSRF tokens and implements secure cookie handling with JWT tokens.
    *   **Recommendation:** You SHOULD add rate limiting specifically to the authentication endpoints in this file. The current login endpoint (lines 69-151) needs brute force protection.

*   **File:** `microblog/utils/logging.py`
    *   **Summary:** This file provides a comprehensive structured logging system with specialized SecurityLogger, PerformanceLogger, and AuditLogger classes. It includes methods for auth failures, CSRF violations, and suspicious activity logging.
    *   **Recommendation:** You MUST use the existing `SecurityLogger` class for security audit logging. It already has methods like `auth_failure()`, `csrf_violation()`, and `permission_denied()` that you should integrate with your rate limiting implementation.

*   **File:** `microblog/server/app.py`
    *   **Summary:** This file sets up the FastAPI application with middleware registration. It already registers the existing security middleware in proper order.
    *   **Recommendation:** You MUST add your new rate limiting middleware to the middleware stack in this file. Follow the existing pattern of middleware registration on lines 85-111.

### Implementation Tips & Notes

*   **Tip:** The project already has a solid foundation for security with JWT authentication, CSRF protection, and structured logging. Your task is to enhance this with rate limiting and additional security headers.

*   **Note:** The architecture specification calls for specific security headers including HSTS and CSP. The current `SecurityHeadersMiddleware` (lines 207-224 in middleware.py) only implements basic headers - you need to add the missing ones from the architecture spec.

*   **Warning:** The project uses FastAPI with Starlette middleware. When implementing rate limiting, ensure you follow the `BaseHTTPMiddleware` pattern used by existing middleware to maintain consistency.

*   **Tip:** The SecurityLogger class already exists and has exactly the methods you need for audit logging. Import and use `get_security_logger()` from `microblog.utils.logging` rather than creating your own logging implementation.

*   **Note:** The authentication endpoints that need rate limiting are in `/auth/login` and `/auth/api/login`. Both handle user authentication and are vulnerable to brute force attacks without rate limiting.

*   **Warning:** The project doesn't currently have any rate limiting dependencies in `pyproject.toml`. You'll need to research appropriate libraries (like `slowapi` for FastAPI rate limiting) and add them to the dependencies.

*   **Tip:** The middleware registration order matters in FastAPI. Rate limiting should typically be applied early in the middleware stack, but after CORS. Study the existing middleware order in `app.py` lines 75-111 for guidance.

*   **Note:** Input sanitization is mentioned in the architecture but the current markdown processor already handles HTML escaping. Focus on validating and sanitizing user inputs in forms and API endpoints rather than duplicating existing markdown sanitization.