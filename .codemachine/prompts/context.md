# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I6.T4",
  "iteration_id": "I6",
  "iteration_goal": "Implement production features, security hardening, deployment support, comprehensive documentation, and final system testing",
  "description": "Implement performance optimizations including template caching, static asset optimization, database query optimization, and build process improvements.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Performance requirements, optimization strategies, caching patterns",
  "target_files": ["microblog/utils/cache.py", "microblog/builder/template_renderer.py", "microblog/builder/generator.py"],
  "input_files": ["microblog/builder/template_renderer.py", "microblog/builder/generator.py"],
  "deliverables": "Template caching system, asset optimization, query optimization, build improvements, performance monitoring",
  "acceptance_criteria": "Build times meet performance targets (<5s for 100 posts), template rendering optimized, asset delivery efficient, performance monitoring functional",
  "dependencies": ["I3.T5", "I3.T3"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: scalability-performance (from 05_Operational_Architecture.md)

```markdown
**Scalability & Performance:**

**Performance Optimization:**
- **Static Content Delivery**: Pre-generated HTML eliminates server processing overhead
- **Efficient File I/O**: Optimized markdown parsing and template rendering
- **Database Optimization**: Single-user SQLite with minimal query complexity
- **Asset Optimization**: Minified CSS and vendored JavaScript for reduced load times
- **Caching Strategy**: Browser caching headers for static content

**Build Performance:**
```python
# Build performance targets
BUILD_PERFORMANCE_TARGETS = {
    "100_posts": "< 5 seconds",
    "1000_posts": "< 30 seconds",
    "markdown_parsing": "< 100ms per file",
    "template_rendering": "< 50ms per page",
    "image_copying": "< 1GB per minute"
}
```

**Scalability Considerations:**
- **Horizontal Scaling**: Static output enables CDN distribution and geographic scaling
- **Vertical Scaling**: Single-threaded build process can utilize multiple CPU cores for file processing
- **Storage Scaling**: File system architecture supports unlimited content growth
- **Traffic Scaling**: Static site delivery handles unlimited concurrent readers

**Performance Monitoring:**
- **Build Time Tracking**: Monitoring build duration and identifying bottlenecks
- **API Response Times**: Dashboard endpoint performance measurement
- **Resource Usage**: Memory and CPU utilization during build processes
- **File System Performance**: I/O operation timing and throughput measurement
```

### Context: architectural-style (from 02_Architecture_Overview.md)

```markdown
**Primary Style: Hybrid Static-First Architecture with Separation of Concerns**

The MicroBlog system employs a hybrid architectural approach that combines static site generation with a dynamic management interface. This design separates the public-facing blog (served as static files) from the administrative interface (dynamic web application), providing optimal performance for readers while maintaining ease of management for content creators.

**Key Architectural Patterns:**

1. **Static-First Generation**: The public blog is generated as static HTML files, ensuring maximum performance, security, and deployment flexibility. This eliminates runtime dependencies for content delivery and enables hosting on any static file server.

2. **Layered Monolith for Management**: The dashboard and build system follow a layered architecture pattern with clear separation between presentation (HTMX-enhanced web interface), business logic (content management and site generation), and data access (filesystem and SQLite) layers.

3. **Command-Query Separation**: Clear distinction between read operations (serving static content, dashboard views) and write operations (content modification, site rebuilds) with appropriate performance optimizations for each.

4. **Progressive Enhancement**: The dashboard uses HTMX for enhanced interactivity while maintaining functionality without JavaScript, ensuring accessibility and reliability.

**Rationale for Architectural Choice:**

- **Performance**: Static files provide sub-100ms page loads and can handle high traffic without server resources
- **Simplicity**: Monolithic dashboard avoids distributed system complexity while maintaining clear internal boundaries
- **Deployment Flexibility**: Static output can be deployed anywhere (CDN, static hosts, traditional servers)
- **Developer Experience**: Clear separation enables focused development on each concern without cross-cutting complexity
- **Reliability**: Atomic builds with rollback capabilities ensure consistent site state
- **Security**: Static content eliminates many attack vectors; dynamic interface has minimal surface area
```

### Context: task-i3-t3 (from 02_Iteration_I3.md)

```markdown
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

### Context: task-i3-t5 (from 02_Iteration_I3.md)

```markdown
*   **Task 3.5:**
    *   **Task ID:** `I3.T5`
    *   **Description:** Create main build generator that orchestrates the complete build process with atomic operations, backup creation, and rollback capability. Implement build status tracking and progress reporting.
    *   **Agent Type Hint:** `BackendAgent`
    *   **Inputs:** Build orchestration requirements, atomic build strategy, safety mechanisms
    *   **Input Files:** ["microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "microblog/builder/asset_manager.py", "docs/diagrams/build_process.puml"]
    *   **Target Files:** ["microblog/builder/generator.py"]
    *   **Deliverables:** Build orchestrator, atomic build implementation, backup/rollback system, progress tracking
    *   **Acceptance Criteria:** Build completes atomically (success or rollback), backup created before build, rollback works on failure, progress tracking functional
    *   **Dependencies:** `I3.T2`, `I3.T3`, `I3.T4`
    *   **Parallelizable:** No
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** This file contains the complete template rendering system with Jinja2 engine, context management, and various rendering methods for different page types. It includes custom filters and globals but currently lacks any caching mechanism.
    *   **Recommendation:** You MUST enhance this file to add template caching functionality. The current implementation creates a new Jinja2 environment on each instantiation and doesn't cache rendered templates. Focus on implementing template compilation caching and potentially rendered output caching for frequently accessed templates.

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** This file contains the main build orchestrator that coordinates the complete build process with atomic operations, backup/rollback, and progress tracking. It's well-structured but lacks performance optimizations for large numbers of posts.
    *   **Recommendation:** You MUST optimize the build process here by adding parallel processing capabilities, batch operations, and build performance monitoring. The current implementation processes posts sequentially which could be a bottleneck for large sites.

*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains comprehensive configuration management with Pydantic models, YAML parsing, validation, and hot-reload support. It already has monitoring configuration but lacks specific performance/caching configuration.
    *   **Recommendation:** You SHOULD extend the configuration model to include caching-specific settings like cache sizes, TTL values, and performance monitoring thresholds.

### Implementation Tips & Notes

*   **Tip:** The codebase uses a global singleton pattern for major components (see `get_template_renderer()`, `get_build_generator()` functions). You SHOULD follow this pattern when implementing the cache module.

*   **Note:** The build system has specific performance targets defined in the architecture: `<5s for 100 posts`, `<30s for 1000 posts`, `<100ms per file for markdown parsing`, `<50ms per page for template rendering`. Your optimizations MUST be designed to meet these targets.

*   **Warning:** The build system includes atomic operations with backup/rollback functionality. Ensure your performance optimizations do not compromise the integrity of the atomic build process or the backup/rollback mechanisms.

*   **Tip:** The template renderer already has a Jinja2 environment with custom filters and globals. When implementing caching, you SHOULD cache the compiled templates and rendered output separately to maximize performance gains while maintaining flexibility.

*   **Note:** The monitoring system is already implemented (`microblog/utils/monitoring.py`) and the configuration supports monitoring settings. You SHOULD integrate your performance optimizations with the existing monitoring infrastructure to track cache hit rates, build times, and performance metrics.

*   **Warning:** The codebase follows strict type hints and uses Pydantic for validation. Ensure all your new code follows these patterns and includes proper type annotations and validation where appropriate.

*   **Tip:** The build generator already has a progress reporting system with callbacks. You SHOULD integrate your performance monitoring with this existing progress tracking to provide real-time performance feedback during builds.