# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T2",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Implement markdown processor with python-markdown and pymdown-extensions. Support YAML frontmatter parsing, syntax highlighting, and content validation.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Markdown processing requirements, frontmatter specification, content validation rules",
  "target_files": ["microblog/builder/markdown_processor.py"],
  "input_files": ["microblog/content/post_service.py"],
  "deliverables": "Markdown processing engine with frontmatter support, syntax highlighting, content validation",
  "acceptance_criteria": "Markdown renders to HTML correctly, YAML frontmatter extracts properly, syntax highlighting works, content validation catches errors",
  "dependencies": ["I2.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: task-i3-t2 (from 02_Iteration_I3.md)

```markdown
<!-- anchor: task-i3-t2 -->
*   **Task 3.2:**
    *   **Task ID:** `I3.T2`
    *   **Description:** Implement markdown processor with python-markdown and pymdown-extensions. Support YAML frontmatter parsing, syntax highlighting, and content validation.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Markdown processing requirements, frontmatter specification, content validation rules
    *   **Input Files:** ["microblog/content/post_service.py"]
    *   **Target Files:** ["microblog/builder/markdown_processor.py"]
    *   **Deliverables:** Markdown processing engine with frontmatter support, syntax highlighting, content validation
    *   **Acceptance Criteria:** Markdown renders to HTML correctly, YAML frontmatter extracts properly, syntax highlighting works, content validation catches errors
    *   **Dependencies:** `I2.T4`
    *   **Parallelizable:** Yes
```

### Context: iteration-3-plan (from 02_Iteration_I3.md)

```markdown
<!-- anchor: iteration-3-plan -->
### Iteration 3: Static Site Generation & Build System

*   **Iteration ID:** `I3`
*   **Goal:** Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback
*   **Prerequisites:** `I2` (Authentication and core models completed)
*   **Tasks:**
```

### Context: key-entities (from 03_System_Structure_and_Data.md)

```markdown
<!-- anchor: key-entities -->
**Key Entities:**

1. **User**: Single admin user with authentication credentials (stored in SQLite)
2. **Post**: Blog posts with metadata and content (stored as markdown files with YAML frontmatter)
3. **Image**: Media files referenced in posts (stored in filesystem with metadata tracking)
4. **Configuration**: System settings and blog metadata (stored as YAML configuration file)
5. **Session**: Authentication sessions (stateless JWT tokens, no persistent storage)
```

### Context: data-model-diagram (from 03_System_Structure_and_Data.md)

```markdown
entity "Post File" as post {
  --
  **Frontmatter (YAML)**
  title : VARCHAR(200)
  date : DATE
  slug : VARCHAR(200) <<optional>>
  tags : ARRAY[VARCHAR]
  draft : BOOLEAN = false
  description : VARCHAR(300)
  --
  **Content (Markdown)**
  content : TEXT
  --
  **File Metadata**
  file_path : VARCHAR(500)
  created_at : TIMESTAMP
  modified_at : TIMESTAMP
}
```

### Context: data-storage-strategy (from 03_System_Structure_and_Data.md)

```markdown
<!-- anchor: data-storage-strategy -->
**Data Storage Strategy:**

**SQLite Database (microblog.db):**
- Stores single user authentication record
- Lightweight, serverless, no external dependencies
- Automatic schema creation on first run
- Handles concurrent read access (dashboard operations)

**File System Storage (content/):**
- Markdown files with YAML frontmatter for posts
- Images stored in organized directory structure
- Configuration as human-readable YAML
- Version control friendly (Git integration possible)
- Direct file system access for build process

**Generated Output (build/):**
- Static HTML, CSS, and JavaScript files
- Copied and optimized images
- RSS feed and sitemap generation
- Atomic generation with backup/rollback
- Deployable to any static file server
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code
*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file contains the complete PostService class that manages blog posts with filesystem storage, including CRUD operations, frontmatter parsing, and file handling. It already has a working `_parse_markdown_file` method that parses YAML frontmatter.
    *   **Recommendation:** You MUST study this file carefully as it shows the expected frontmatter structure and how posts are loaded/parsed. The PostService already handles frontmatter parsing with regex and yaml.safe_load(). Your markdown processor should complement this by focusing on the markdown-to-HTML conversion.

*   **File:** `microblog/content/validators.py`
    *   **Summary:** This file defines the PostFrontmatter and PostContent dataclasses used throughout the system for validating blog post structure and metadata.
    *   **Recommendation:** You SHOULD import and use these validation classes in your markdown processor. The PostContent and PostFrontmatter models are the standard data structures expected by the rest of the system.

*   **File:** `pyproject.toml`
    *   **Summary:** The project dependencies already include `markdown>=3.5.0` and `pymdown-extensions>=10.0.0`, exactly what you need for this task.
    *   **Recommendation:** You can directly import and use these libraries - they are already installed and configured as project dependencies.

*   **File:** `microblog/builder/__init__.py`
    *   **Summary:** This is the builder package where your markdown processor will live. It's currently just a package docstring describing static site generation components.
    *   **Recommendation:** Your new `markdown_processor.py` file should go in this directory alongside the existing `__init__.py`.

### Implementation Tips & Notes
*   **Tip:** The PostService already has frontmatter parsing logic in `_parse_markdown_file()` method using regex pattern `r'^---\s*\n(.*?)\n---\s*\n(.*)$'` and `yaml.safe_load()`. You should use a similar or compatible approach in your processor.
*   **Note:** The project uses structured logging with the `logging` module. Follow the same pattern by getting a logger with `logger = logging.getLogger(__name__)` at the module level.
*   **Warning:** The PostService expects date objects to be converted to/from ISO strings when serializing YAML. Your processor should handle date objects properly for consistency.
*   **Code Style:** The project uses dataclasses, type hints, and follows the existing patterns seen in other modules. Follow the same conventions with proper docstrings and error handling.
*   **Validation Integration:** The existing code uses `validate_post_content()` function from validators.py - your markdown processor should work with these validated PostContent objects.
*   **Directory Structure:** Content is stored in `content/posts/` directory, and the project expects markdown files with `.md` extension and specific filename patterns like `YYYY-MM-DD-slug.md`.
*   **Dependencies:** The project already includes python-frontmatter in dependencies, but the current PostService uses manual YAML parsing instead. You could choose either approach, but should remain consistent with existing patterns.

### Strategic Recommendations
*   **Primary Goal:** Create a markdown processor that takes validated PostContent objects and converts the markdown content to HTML with syntax highlighting, while preserving the frontmatter structure.
*   **Integration Point:** Your processor should work seamlessly with the existing PostService and validation system - don't duplicate frontmatter parsing logic.
*   **Error Handling:** Follow the existing exception patterns (PostFileError, PostValidationError) defined in post_service.py for consistency.
*   **Testing:** The project has a comprehensive test suite in `tests/unit/` - you should design your processor to be easily testable with similar patterns.