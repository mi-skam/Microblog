# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T6",
  "iteration_id": "I2",
  "iteration_goal": "Implement authentication system with JWT tokens, user management, and core data models for posts and images",
  "description": "Add CLI command for user creation and management. Implement interactive user setup for initial system configuration.",
  "agent_type_hint": "BackendAgent",
  "inputs": "CLI framework from I1.T1, user creation requirements, interactive command patterns",
  "target_files": ["microblog/cli.py"],
  "input_files": ["microblog/cli.py", "microblog/auth/models.py"],
  "deliverables": "CLI user creation command, interactive setup process, user management utilities",
  "acceptance_criteria": "`microblog create-user` works interactively, password validation implemented, user creation success/failure feedback provided",
  "dependencies": ["I2.T3"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: CLI Interface (from 01_Plan_Overview_and_Setup.md)

```markdown
*   **CLI Interface**: Commands for build, serve, user creation, and system management
```

### Context: Directory Structure - CLI Module (from 01_Plan_Overview_and_Setup.md)

```markdown
│   ├── cli.py                      # Click-based CLI interface
```

### Context: Technology Stack - CLI Framework (from 01_Plan_Overview_and_Setup.md)

```markdown
    *   CLI: Click for command-line interface and management tools
```

### Context: Task I1.T1 - CLI Framework Foundation (from 02_Iteration_I1.md)

```markdown
    *   **Task 1.1:**
        *   **Task ID:** `I1.T1`
        *   **Description:** Initialize project structure, Python package setup, and basic CLI framework with Click. Create all necessary directories and files, set up pyproject.toml with dependencies, and implement basic CLI commands for build and serve operations.
        *   **Agent Type Hint:** `SetupAgent`
        *   **Inputs:** Project directory structure definition from Section 3, technology stack requirements from Section 2
        *   **Input Files:** [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"]
        *   **Target Files:** ["pyproject.toml", "requirements.txt", "microblog/__init__.py", "microblog/cli.py", "README.md", ".gitignore", "Makefile", "Dockerfile", "docker-compose.yml"]
        *   **Deliverables:** Complete Python package structure, installable CLI tool, dependency management setup, development environment configuration, basic documentation
        *   **Acceptance Criteria:** CLI tool installs successfully, `microblog --help` displays command structure, all directories created, dependencies resolve without conflicts, Docker setup functional
        *   **Dependencies:** None
        *   **Parallelizable:** No
```

### Context: Task I2.T6 - Current Task Specification (from 02_Iteration_I2.md)

```markdown
    *   **Task 2.6:**
        *   **Task ID:** `I2.T6`
        *   **Description:** Add CLI command for user creation and management. Implement interactive user setup for initial system configuration.
        *   **Agent Type Hint:** `BackendAgent`
        *   **Inputs:** CLI framework from I1.T1, user creation requirements, interactive command patterns
        *   **Input Files:** ["microblog/cli.py", "microblog/auth/models.py"]
        *   **Target Files:** ["microblog/cli.py"]
        *   **Deliverables:** CLI user creation command, interactive setup process, user management utilities
        *   **Acceptance Criteria:** `microblog create-user` works interactively, password validation implemented, user creation success/failure feedback provided
        *   **Dependencies:** `I2.T3`
        *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/cli.py`
    *   **Summary:** This file contains the Click-based CLI framework with existing commands for build, serve, status, and a stub for create-user. The create-user command structure is already defined but contains placeholder TODO implementation.
    *   **Recommendation:** You MUST complete the implementation of the existing `create_user` function (lines 98-129). Do NOT create a new command - the command structure, arguments, and Click decorators are already correctly implemented.

*   **File:** `microblog/auth/models.py`
    *   **Summary:** This file contains the complete User model with SQLite database integration. It provides the `User.create_user()` class method and includes single-user constraint enforcement.
    *   **Recommendation:** You MUST import and use the `User` class from this file. The `User.create_user()` method handles the actual user creation and database operations.

*   **File:** `microblog/auth/password.py`
    *   **Summary:** This file provides password hashing utilities with bcrypt using the required cost factor of 12. It includes validation and secure hashing functions.
    *   **Recommendation:** You SHOULD import `hash_password` from this file if you need to manually hash passwords, but note that the database utility functions already handle this.

*   **File:** `microblog/database.py`
    *   **Summary:** This file provides high-level database management utilities including `create_admin_user()`, `get_database_path()`, `init_database()`, and validation functions. This is the primary interface for user management operations.
    *   **Recommendation:** You MUST use the `create_admin_user()` function from this file for user creation. It handles database initialization, password hashing, validation, and provides comprehensive error handling.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file contains utility functions including directory management and project root detection.
    *   **Recommendation:** You MAY need to import utilities from this file if you need path management, but the database utilities already handle most directory operations.

### Implementation Tips & Notes

*   **Tip:** The CLI command structure is already complete in `microblog/cli.py` with proper Click decorators, argument prompting, and password confirmation. You only need to replace the TODO implementation (lines 123-128).

*   **Note:** The `create_admin_user()` function in `microblog/database.py` provides comprehensive validation including length checks, empty field validation, and minimum password length (8 characters). Use this function rather than calling User methods directly.

*   **Warning:** The system enforces a single-user constraint. The `User.create_user()` method will raise a `ValueError` if a user already exists, unless the `--force` flag is used. You MUST handle this scenario properly in your implementation.

*   **Tip:** For interactive user experience, you should initialize the database if it doesn't exist. Use `init_database()` or `setup_database_if_needed()` from the database module.

*   **Note:** The CLI command already handles password prompting with Click's `prompt=True, hide_input=True, confirmation_prompt=True` configuration. The password parameter will contain the validated, confirmed password.

*   **Warning:** You MUST provide clear success/failure feedback to the user as specified in the acceptance criteria. Use Click's `click.echo()` for user feedback and consider using Click's styling functions for better UX.

*   **Tip:** The `--force` flag is already defined and captured in the function signature. When force=True, you should handle the existing user scenario (possibly by removing the existing user first, though the current User model doesn't support updates - consider the architectural implications).

*   **Note:** All necessary imports for database operations should include: `from microblog.database import create_admin_user, init_database, get_database_info` or similar, depending on your implementation approach.