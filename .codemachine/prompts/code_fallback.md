# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Implement User model with SQLite database, bcrypt password hashing, and JWT token management. Create database schema and user creation utilities.

**Acceptance Criteria:** User creation works correctly, passwords hash with bcrypt cost ≥12, JWT tokens generate and validate properly, database initializes automatically

---

## Issues Detected

**Critical DateTime Handling Issue:**
*   **DateTime Inconsistency:** In `microblog/auth/models.py`, the `create_user` method stores timestamps as ISO format strings, but the `get_by_username` and `get_by_id` methods try to parse them with `datetime.fromisoformat()`. However, SQLite's `CURRENT_TIMESTAMP` returns format like "2024-01-01 12:00:00" which is not ISO format and will cause parsing errors when retrieving users.

**Linting Errors:**
*   **Type Annotations:** Multiple files use `Optional[Type]` instead of modern `Type | None` syntax (21 instances)
*   **Exception Handling:** `microblog/auth/jwt_handler.py:53` raises exceptions without `from err` or `from None`
*   **Missing Newlines:** Missing trailing newlines in `jwt_handler.py`, `models.py`, `password.py`, and `database.py`
*   **Import Issues:** `microblog/auth/models.py` has unused import of `get_project_root`
*   **Import Sorting:** `microblog/auth/password.py` has unsorted imports

---

## Best Approach to Fix

You MUST fix the datetime handling issue and all linting errors:

1. **Fix DateTime Handling:** In `microblog/auth/models.py`, update the `get_by_username` and `get_by_id` methods to properly handle SQLite's datetime format. Either:
   - Convert SQLite timestamps to ISO format during retrieval, OR
   - Use a different parsing method that handles SQLite's default format

2. **Fix All Linting Issues:** Run `python -m ruff check --fix` to automatically fix most linting issues, then manually fix:
   - The exception handling in `jwt_handler.py:53` (add `from None`)
   - Remove the unused `get_project_root` import from `models.py`

3. **Verify Functionality:** After fixes, ensure the datetime retrieval works correctly by testing user creation and retrieval with the actual database.