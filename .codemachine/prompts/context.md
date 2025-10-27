# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T3",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Create Jinja2 template rendering system with base templates for homepage, post pages, archive, tags, and RSS feed. Implement template inheritance and context management.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Template requirements, site structure, Jinja2 best practices",
  "target_files": ["microblog/builder/template_renderer.py", "templates/index.html", "templates/post.html", "templates/archive.html", "templates/tag.html", "templates/rss.xml"],
  "input_files": ["templates/base.html", "microblog/server/config.py"],
  "deliverables": "Template rendering engine, complete template set, context management, RSS feed generation",
  "acceptance_criteria": "Templates render correctly with context, template inheritance works, RSS feed validates, all page types supported",
  "dependencies": ["I3.T2"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: task-i3-t3 (from 02_Iteration_I3.md)

```markdown
<!-- anchor: task-i3-t3 -->
*   **Task 3.3:**
    *   **Task ID:** `I3.T3`
    *   **Description:** Create Jinja2 template rendering system with base templates for homepage, post pages, archive, tags, and RSS feed. Implement template inheritance and context management.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Template requirements, site structure, Jinja2 best practices
    *   **Input Files:** ["templates/base.html", "microblog/server/config.py"]
    *   **Target Files:** ["microblog/builder/template_renderer.py", "templates/index.html", "templates/post.html", "templates/archive.html", "templates/tag.html", "templates/rss.xml"]
    *   **Deliverables:** Template rendering engine, complete template set, context management, RSS feed generation
    *   **Acceptance Criteria:** Templates render correctly with context, template inheritance works, RSS feed validates, all page types supported
    *   **Dependencies:** `I3.T2`
    *   **Parallelizable:** Yes
```

### Context: technology-stack (from 02_Architecture_Overview.md)

```markdown
| **Template Engine** | Jinja2 | Latest | Industry standard with excellent performance, template inheritance, and extensive filter ecosystem. Native FastAPI integration. |
```

### Context: static-generation-strategy (from 02_Architecture_Overview.md)

```markdown
**Static Generation Strategy:**
- Jinja2 templates provide flexibility for custom themes and layouts
- python-markdown offers extensive plugin ecosystem for future enhancements
- Separation of content (markdown) from presentation (templates) enables design iteration
```

### Context: iteration-3-plan (from 02_Iteration_I3.md)

```markdown
### Iteration 3: Static Site Generation & Build System

*   **Iteration ID:** `I3`
*   **Goal:** Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback
*   **Prerequisites:** `I2` (Authentication and core models completed)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains the complete configuration management system with Pydantic models (SiteConfig, BuildConfig, etc.) and hot-reload support. The AppConfig class provides structured access to all site configuration.
    *   **Recommendation:** You MUST import and use the `get_config()` function from this file to access site configuration. The configuration includes `site.title`, `site.url`, `site.author`, `site.description` which are essential for template context.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** This file contains a fully implemented MarkdownProcessor class with python-markdown, pymdown-extensions, syntax highlighting, and validation. It has methods like `process_content()` and `get_toc()` for table of contents.
    *   **Recommendation:** You SHOULD import and use the `get_markdown_processor()` function from this file. The processor can generate HTML content and table of contents that you'll need in your templates.

*   **File:** `microblog/content/post_service.py`
    *   **Summary:** This file provides the PostService class with complete CRUD operations for blog posts, including methods like `list_posts()`, `get_published_posts()`, and post filtering by tags. Posts are structured with frontmatter and content.
    *   **Recommendation:** You MUST import and use the `get_post_service()` function from this file to retrieve post data for templates. The service provides filtered post lists that you'll need for homepage, archive, and tag pages.

*   **File:** `microblog/utils.py`
    *   **Summary:** This file contains utility functions including `get_templates_dir()`, `get_project_root()`, `get_build_dir()`, and `ensure_directory()` for filesystem operations.
    *   **Recommendation:** You SHOULD use these utility functions for path management. `get_templates_dir()` returns the templates directory path, which is essential for Jinja2 template loading.

### Implementation Tips & Notes

*   **Tip:** I confirmed that Jinja2 is already included in the project dependencies (version >=3.1.0) in pyproject.toml. You can import it directly.

*   **Note:** The task specifies `templates/base.html` as an input file, but this file does not exist yet. You will need to create this base template first as the foundation for template inheritance.

*   **Tip:** The PostContent objects from the post service have frontmatter attributes like `title`, `date`, `tags`, `description`, `slug`, and `is_draft`. Use these for template context.

*   **Note:** The configuration system provides site-level information (`site.title`, `site.url`, `site.author`, `site.description`) that should be included in template context for all pages.

*   **Warning:** The templates directory exists but is currently empty except for a dashboard subdirectory. You need to create all template files from scratch following Jinja2 best practices.

*   **Tip:** For RSS feed generation, you'll need to format dates in RFC 2822 format and ensure proper XML escaping. Consider using Jinja2's built-in filters for this.

*   **Note:** The acceptance criteria specifically mentions "template inheritance works" - this means your base.html template should define blocks that other templates extend, following standard Jinja2 patterns.

*   **Tip:** The markdown processor has a `get_toc()` method that returns HTML table of contents - this could be useful for post pages with navigation.