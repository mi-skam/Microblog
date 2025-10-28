# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T4",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Create image upload service with file validation, filename sanitization, and storage management. Implement upload endpoint with progress feedback and markdown snippet generation.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Image management requirements, upload validation, security considerations",
  "target_files": ["microblog/content/image_service.py", "microblog/server/routes/api.py"],
  "input_files": ["microblog/server/config.py"],
  "deliverables": "Image upload service, file validation, storage management, upload endpoint, markdown integration",
  "acceptance_criteria": "File uploads work correctly, validation prevents invalid files, filenames sanitized for security, markdown snippets generated, progress feedback functional",
  "dependencies": ["I5.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: key-entities (from 03_System_Structure_and_Data.md)

```markdown
**Key Entities:**

1. **User**: Single admin user with authentication credentials (stored in SQLite)
2. **Post**: Blog posts with metadata and content (stored as markdown files with YAML frontmatter)
3. **Image**: Media files referenced in posts (stored in filesystem with metadata tracking)
4. **Configuration**: System settings and blog metadata (stored as YAML configuration file)
5. **Session**: Authentication sessions (stateless JWT tokens, no persistent storage)
```

### Context: data-model-diagram (from 03_System_Structure_and_Data.md)

```markdown
entity "Image File" as image {
  --
  **File Metadata**
  filename : VARCHAR(255)
  file_path : VARCHAR(500)
  file_size : INTEGER
  mime_type : VARCHAR(100)
  upload_date : TIMESTAMP
  --
  **References**
  referenced_in_posts : ARRAY[VARCHAR]
}

note top of image : Stored in content/images/\nSupported: jpg, png, gif, webp, svg\nCopied to build/images/
```

### Context: data-storage-strategy (from 03_System_Structure_and_Data.md)

```markdown
**File System Storage (content/):**
- Markdown files with YAML frontmatter for posts
- Images stored in organized directory structure
- Configuration as human-readable YAML
- Version control friendly (Git integration possible)
- Direct file system access for build process
```

### Context: security-considerations (from 05_Operational_Architecture.md)

```markdown
**Input Validation & Sanitization:**
- **Markdown Sanitization**: HTML escaping by default to prevent XSS attacks
- **File Upload Validation**: Extension whitelist, MIME type verification, size limits
- **Path Traversal Prevention**: Filename sanitization and directory boundary enforcement
- **SQL Injection Prevention**: Parameterized queries for all database operations
- **Command Injection Prevention**: No direct shell execution from user input
```

### Context: component-diagram (from 03_System_Structure_and_Data.md)

```markdown
Component(image_service, "Image Management Service", "Python Service", "Handles image upload and organization")

Rel(api_routes, image_service, "Uses")
Rel(image_service, content_repository, "Uses")

note right of post_service : Handles post validation\nMarkdown processing\nDraft/publish logic
```

### Context: task-i5-t4 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.4:**
    *   **Task ID:** `I5.T4`
    *   **Description:** Create image upload service with file validation, filename sanitization, and storage management. Implement upload endpoint with progress feedback and markdown snippet generation.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Image management requirements, upload validation, security considerations
    *   **Input Files:** ["microblog/server/config.py"]
    *   **Target Files:** ["microblog/content/image_service.py", "microblog/server/routes/api.py"]
    *   **Deliverables:** Image upload service, file validation, storage management, upload endpoint, markdown integration
    *   **Acceptance Criteria:** File uploads work correctly, validation prevents invalid files, filenames sanitized for security, markdown snippets generated, progress feedback functional
    *   **Dependencies:** `I5.T1`
    *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/server/routes/api.py`
    *   **Summary:** This file contains existing HTMX API endpoints for post operations, including a well-established pattern for HTML fragment responses, error handling, and authentication.
    *   **Recommendation:** You MUST follow the same patterns used in this file for HTMX responses. The file already imports `require_authentication` from middleware, uses `HTMLResponse`, and implements error/success fragment helpers. ADD your image upload endpoint here using the same conventions.

*   **File:** `microblog/builder/asset_manager.py`
    *   **Summary:** This file contains comprehensive file validation, security checks, and asset management logic. It includes allowed file extensions, MIME type checking, size limits (50MB), and security validation for images.
    *   **Recommendation:** You MUST reuse the validation logic from `AssetManager.validate_file()` method. This method already handles extension validation (`.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`, `.ico`, `.bmp`), file size limits, MIME type checking, and security filters.

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file provides configuration management but currently doesn't include upload-specific settings like file size limits or allowed extensions.
    *   **Recommendation:** You SHOULD extend the configuration classes to add image upload settings if needed, but the AssetManager already has sensible defaults you can use.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file contains utility functions for directory management (`ensure_directory`) and path handling (`get_content_dir`).
    *   **Recommendation:** You MUST use `get_content_dir()` to construct paths to the images directory and `ensure_directory()` to create directories as needed.

### Implementation Tips & Notes
*   **Tip:** The project already has `python-multipart` and `aiofiles` dependencies installed (from pyproject.toml), which are perfect for handling file uploads with FastAPI.
*   **Note:** The existing API endpoints use Form fields and return HTMLResponse with specific HTMX patterns. Your image upload endpoint should follow this exact pattern for consistency.
*   **Warning:** The AssetManager already defines security validation that prevents executable files, checks MIME types, and validates file extensions. You MUST reuse this logic rather than implementing your own.
*   **Tip:** The content/images/ directory already exists and the AssetManager is configured to copy files from there to build/images/ during site generation.
*   **Note:** For markdown snippet generation, you should generate relative URLs that will work both in the dashboard preview and the final static site (e.g., `/images/filename.jpg`).
*   **Security:** Follow the existing pattern of requiring authentication with `require_authentication(request)` and ensure CSRF protection is handled by the middleware.
*   **Pattern:** Use the existing `_create_error_fragment()` and `_create_success_fragment()` helper functions for consistent HTMX responses.