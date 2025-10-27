# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Create comprehensive unit tests for authentication system, user management, and post data models. Ensure security features are thoroughly tested.

Target files: ["tests/unit/test_auth.py", "tests/unit/test_jwt.py", "tests/unit/test_post_service.py"]

Acceptance criteria: All auth functions tested, JWT generation/validation tested, post operations tested, test coverage >85%, security edge cases covered

---

## Issues Detected

*   **Test Coverage Issue:** Test coverage is only 55% which is significantly below the required 85%. Many critical modules have 0% coverage including CLI, database, middleware, and auth routes.

*   **Database Test Errors:** 14 database-related test errors due to permission issues with temporary database files. The tests are not properly creating isolated temporary databases.

*   **JWT Test Failures:** 4 critical JWT test failures including `test_refresh_token_valid`, `test_refresh_token_config_error`, and `test_full_token_lifecycle` indicating the refresh token functionality is not working correctly.

*   **Post Service Test Failures:** 12 post service test failures including tag filtering, draft handling, and basic CRUD operations, suggesting the tests don't match the actual API.

*   **User Model Test Failure:** 1 failure in `test_parse_datetime_sqlite_format` indicating datetime parsing tests don't match the actual implementation.

*   **Linting Errors:** 16 linting errors including missing newlines, unused variables (`time_diff`, `original_post`, `post`), unused imports (`datetime`, `yaml`, `PostContent`, `PostFrontmatter`), and import redefinitions.

*   **API Mismatches:** Tests are calling methods that don't exist or have different signatures than the actual implementation, particularly in post service tag filtering and JWT refresh functionality.

---

## Best Approach to Fix

You MUST completely rewrite the test files to fix these critical issues:

1. **Fix Database Test Infrastructure:** Replace the temp database fixtures with proper isolated database setup that doesn't have permission issues. Use the existing `conftest.py` patterns and ensure tests properly clean up after themselves.

2. **Match Actual API Signatures:** Review the actual implementation files (`microblog/auth/models.py`, `microblog/auth/jwt_handler.py`, `microblog/content/post_service.py`) to ensure test method calls match the real API signatures and return values.

3. **Fix JWT Refresh Implementation:** The JWT refresh token tests are failing because they don't match the actual `refresh_token` function behavior. Review the actual implementation and fix the test expectations.

4. **Fix Post Service API Calls:** Multiple post service tests are failing due to incorrect method calls. Review the actual `PostService` class and ensure tests call the correct methods with proper parameters.

5. **Fix All Linting Issues:** Remove unused variables and imports, add missing newlines, fix import organization, and eliminate redefined imports.

6. **Increase Test Coverage:** Add tests for missing functionality to reach >85% coverage. Focus on testing middleware, database operations, and authentication flows that are currently at 0% coverage.

7. **Fix DateTime Parsing:** The SQLite datetime parsing test needs to match the actual `_parse_datetime` method implementation.

8. **Proper Test Isolation:** Ensure all tests use proper mocking and temporary resources to avoid file system permission issues and test interference.