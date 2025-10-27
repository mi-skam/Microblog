# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Create main build generator that orchestrates the complete build process with atomic operations, backup creation, and rollback capability. Implement build status tracking and progress reporting.

**Acceptance Criteria**: Build completes atomically (success or rollback), backup created before build, rollback works on failure, progress tracking functional

---

## Issues Detected

*   **Linting Error**: Import `Callable` from `collections.abc` instead of `typing` (UP035 error on line 15)
*   **Linting Error**: Missing newline at end of file (W292 error at line 721)

---

## Best Approach to Fix

You MUST fix the linting errors in `microblog/builder/generator.py`:

1. Replace `from typing import Any, Callable` with `from typing import Any` and add `from collections.abc import Callable` on line 15
2. Add a newline at the end of the file after line 721 (`return generator.build()`)

These are simple formatting fixes that will make the code pass linting checks. The functional implementation is correct and complete according to all task requirements.