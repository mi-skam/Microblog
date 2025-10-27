# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T4",
  "iteration_id": "I4",
  "iteration_goal": "Implement FastAPI web application with HTMX-enhanced dashboard for content management, authentication UI, and basic CRUD operations",
  "description": "Implement authentication routes for login and logout with form handling, CSRF protection, and session management. Create login template with proper security features.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Authentication flow, login form requirements, security best practices",
  "target_files": ["microblog/server/routes/auth.py", "templates/dashboard/login.html"],
  "input_files": ["microblog/server/routes/auth.py", "templates/dashboard/layout.html"],
  "deliverables": "Login/logout routes, authentication templates, form handling, security features",
  "acceptance_criteria": "Login form works correctly, CSRF protection active, sessions manage properly, logout clears cookies, error handling functional",
  "dependencies": ["I2.T5", "I4.T3"],
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

### Context: api-endpoints-detail (from 04_Behavior_and_Communication.md)

```markdown
**Authentication Endpoints:**
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin&password=secret&csrf_token=...
Response: 302 Redirect + Set-Cookie: jwt=...; HttpOnly; Secure; SameSite=Strict

POST /auth/logout
Response: 302 Redirect + Set-Cookie: jwt=; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```
```

### Context: error-handling-api (from 04_Behavior_and_Communication.md)

```markdown
**Standard HTTP Status Codes:**
- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data or validation errors
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: CSRF token invalid or insufficient permissions
- `404 Not Found`: Requested resource does not exist
- `422 Unprocessable Entity`: Validation errors with detailed field information
- `500 Internal Server Error`: Unexpected server error
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/routes/auth.py`
    *   **Summary:** This file ALREADY contains complete authentication route implementations including login, logout, and session management endpoints with full CSRF protection and JWT handling.
    *   **Recommendation:** The authentication routes are ALREADY FULLY IMPLEMENTED. You should NOT modify this file as it already provides all required functionality including login/logout routes, CSRF protection, session management, and both form-based and API endpoints.

*   **File:** `templates/dashboard/layout.html`
    *   **Summary:** This file contains the dashboard base template with Pico.css styling, navigation structure, CSRF token handling, and user menu with logout functionality.
    *   **Recommendation:** You MUST use this as the base template for the login page. The layout includes CSRF token meta tag setup and HTMX configuration that you should leverage.

*   **File:** `microblog/server/middleware.py`
    *   **Summary:** This file contains comprehensive authentication and CSRF protection middleware with JWT validation, secure cookie handling, and proper security headers.
    *   **Recommendation:** You MUST import and use the helper functions from this file: `get_csrf_token()`, `get_current_user()`, and `validate_csrf_from_form()`. These are already being used in the auth routes.

### Implementation Tips & Notes

*   **Critical Discovery:** The authentication routes in `microblog/server/routes/auth.py` are ALREADY FULLY IMPLEMENTED and functional. The file contains:
    - GET /auth/login endpoint that renders login page with CSRF token
    - POST /auth/login endpoint with complete authentication logic, CSRF validation, and secure JWT cookie setting
    - POST /auth/logout endpoint with CSRF validation and proper cookie clearing
    - Additional API endpoints for JSON responses
    - Proper error handling and security features

*   **Missing Component:** The ONLY missing piece is the login template file that the auth routes expect to find. The routes reference `"auth/login.html"` template path.

*   **Template Structure Required:** You need to create `templates/auth/login.html` based on the template path used in the auth routes. You will also need to create the `templates/auth/` directory first.

*   **CSRF Integration:** The login template MUST include a CSRF token field. The auth routes already generate and validate CSRF tokens using `get_csrf_token(request)` and `validate_csrf_from_form()`.

*   **Styling Consistency:** Use Pico.css classes for consistent styling with the dashboard layout. The dashboard layout template shows the proper Pico.css structure to follow.

*   **Security Requirements:** The template must include proper form validation, error message display, and secure form submission following the existing patterns in the codebase.

*   **Template Location:** Create the template at `templates/auth/login.html` since that's exactly what the auth routes expect. You'll need to create the `templates/auth/` directory first as it doesn't exist yet.

*   **Template Inheritance:** The login template should NOT extend from `dashboard/layout.html` since it's a standalone authentication page that users see before they're logged in. Create a simpler template structure focused on the login form.

*   **Logout Template:** The auth routes also reference an `"auth/logout.html"` template for GET requests to `/auth/logout`. You may need to create this as well, but the task only specifically mentions the login template.