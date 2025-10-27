# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Implement post editing interface with markdown textarea, metadata fields, and form validation. Create post creation and editing templates with proper form handling.

**Target Files:** ["templates/dashboard/post_edit.html", "microblog/server/routes/dashboard.py"]
**Input Files:** ["microblog/content/post_service.py", "templates/dashboard/layout.html"]
**Deliverables:** Post editing interface, form validation, metadata management, create/edit templates
**Acceptance Criteria:** Post creation form works, editing loads existing posts, validation prevents invalid data, draft/publish status manageable

---

## Issues Detected

*   **Form Field Name Mismatch:** The API endpoint `/api/posts/{slug}` expects parameter `new_slug: str = Form("")` but the template form field is named `slug`. This causes the slug update functionality to fail silently.
*   **Linting Error:** Import organization issues - imports are not sorted or properly formatted in `microblog/server/routes/dashboard.py`.
*   **Linting Error:** Unused import `datetime.date` in `microblog/server/routes/dashboard.py` line 9.
*   **Linting Error:** Unused import `microblog.utils.get_content_dir` in `microblog/server/routes/dashboard.py` line 17.
*   **Linting Error:** Module level import `from pathlib import Path` not at top of file in line 25.
*   **Linting Error:** Parameter name `date` conflicts with imported `date` from datetime module, causing variable shadowing in both API endpoints.
*   **Linting Error:** Missing proper exception chaining with `raise ... from err` in all exception handlers in the API endpoints.

---

## Best Approach to Fix

You MUST fix the form field name mismatch and all linting errors:

1. **Fix form field name mismatch:** Either change the template form field name from `slug` to `new_slug` in `templates/dashboard/post_edit.html` line 35, OR change the API parameter from `new_slug` to `slug` in the update endpoint. Recommend changing the template to use `new_slug` to match the API.

2. **Fix all linting errors:**
   - Remove unused imports (`date` and `get_content_dir`)
   - Move `from pathlib import Path` to top of file with other imports
   - Rename the `date` parameter to `post_date` in both API endpoints to avoid name conflict
   - Add proper exception chaining using `raise ... from e` in all exception handlers
   - Organize all imports properly

3. **Run `python -m ruff check --fix .` to automatically fix fixable linting issues**, then manually fix the remaining issues listed above.