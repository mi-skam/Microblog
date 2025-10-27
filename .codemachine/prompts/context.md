# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T5",
  "iteration_id": "I3",
  "iteration_goal": "Implement core static site generator with template rendering, markdown processing, and atomic build system with backup/rollback",
  "description": "Create main build generator that orchestrates the complete build process with atomic operations, backup creation, and rollback capability. Implement build status tracking and progress reporting.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Build orchestration requirements, atomic build strategy, safety mechanisms",
  "target_files": ["microblog/builder/generator.py"],
  "input_files": ["microblog/builder/markdown_processor.py", "microblog/builder/template_renderer.py", "microblog/builder/asset_manager.py", "docs/diagrams/build_process.puml"],
  "deliverables": "Build orchestrator, atomic build implementation, backup/rollback system, progress tracking",
  "acceptance_criteria": "Build completes atomically (success or rollback), backup created before build, rollback works on failure, progress tracking functional",
  "dependencies": ["I3.T2", "I3.T3", "I3.T4"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Reliability & Availability - Atomic Build Strategy (from 05_Operational_Architecture.md)

```markdown
**Reliability & Availability:**

**Fault Tolerance:**
- **Atomic Builds**: Complete success or complete rollback for site generation
- **Backup Strategy**: Automatic backup creation before each build operation
- **Rollback Capability**: Instant restoration to previous working state on build failure
- **Error Recovery**: Graceful handling of file system and permission errors
- **Data Integrity**: Validation of content files and configuration during processing

**High Availability Design:**
```python
# Build safety implementation
def atomic_build():
    backup_current_build()  # Preserve working state
    try:
        generate_new_build()  # Create complete new build
        validate_build_output()  # Verify build integrity
        activate_new_build()  # Atomic swap to new version
    except Exception as e:
        restore_from_backup()  # Rollback on any failure
```

### Context: Build Process Requirements (from 02_Iteration_I3.md)

```markdown
**Task 3.5:**
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

### Context: Build Process Diagram Requirements (from build_process.puml)

```markdown
**Atomic Build Safety Strategy:**

1. **Backup Creation**: Existing build/ moved to build.bak/ before starting
2. **Fresh Build**: New build/ directory created for clean generation
3. **Phase Isolation**: Each phase (content, templates, assets) is independent
4. **Error Handling**: Any failure triggers immediate rollback
5. **Integrity Verification**: Build output validated before finalization
6. **Cleanup**: Backup removed only after successful completion

**Directory States:**
- Pre-build: build/ (current), build.bak/ (previous backup)
- During build: build/ (new), build.bak/ (current backup)
- Success: build/ (new), build.bak/ (removed)
- Failure: build/ (restored from backup), build.bak/ (removed)
```

### Context: Performance Requirements (from 01_Context_and_Drivers.md)

```markdown
**Performance Requirements:**
- Generated HTML pages must be <100KB uncompressed (excluding images)
- Full site rebuild with 100 posts must complete in <5 seconds
- Full site rebuild with 1,000 posts should complete in <30 seconds
- HTMX API endpoints must respond in <200ms for read operations
- Configuration changes must be detected and applied within 2 seconds (dev mode)

**Reliability Requirements:**
- Build process must be idempotent (identical output for identical input)
- Failed builds must not leave the site in a broken state
- Previous build must be preserved until new build completes successfully
- System must handle missing directories by creating required structure
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `microblog/builder/generator.py`
    *   **Summary:** This file already contains a complete implementation of the BuildGenerator class with all required atomic build functionality, backup/rollback mechanisms, and progress tracking.
    *   **Recommendation:** The task is already completed! The file contains a comprehensive 721-line implementation that fully satisfies all acceptance criteria.

*   **File:** `microblog/builder/markdown_processor.py`
    *   **Summary:** This file contains the MarkdownProcessor class for converting posts to HTML with python-markdown and pymdown-extensions.
    *   **Recommendation:** The generator already imports and uses this via `get_markdown_processor()` for content processing.

*   **File:** `microblog/builder/template_renderer.py`
    *   **Summary:** This file contains the TemplateRenderer class with Jinja2 engine and context management for rendering all site templates.
    *   **Recommendation:** The generator already imports and uses this via `get_template_renderer()` for template rendering.

*   **File:** `microblog/builder/asset_manager.py`
    *   **Summary:** This file contains the AssetManager class for copying images and static files with validation and security checks.
    *   **Recommendation:** The generator already imports and uses this via `get_asset_manager()` for asset copying.

*   **File:** `docs/diagrams/build_process.puml`
    *   **Summary:** Complete PlantUML sequence diagram showing the atomic build workflow with backup creation and rollback mechanisms.
    *   **Recommendation:** The generator implementation follows this diagram exactly.

### Implementation Tips & Notes

*   **CRITICAL:** The task I3.T5 appears to be already completed! The `microblog/builder/generator.py` file contains a comprehensive BuildGenerator class with:
    - Atomic build operations with backup and rollback
    - Complete progress tracking with BuildPhase enum and BuildProgress dataclass
    - Comprehensive error handling and logging
    - Build integrity verification
    - All required phases: initialization, backup creation, content processing, template rendering, asset copying, verification, cleanup, and rollback

*   **Note:** The implementation includes all acceptance criteria:
    - Build completes atomically (success or rollback) ✓
    - Backup created before build ✓
    - Rollback works on failure ✓
    - Progress tracking functional ✓

*   **Architecture:** The generator follows the exact sequence from the build_process.puml diagram and integrates with all dependency components (markdown processor, template renderer, asset manager).

*   **Configuration:** The build uses configuration from `microblog/server/config.py` which specifies `output_dir: build` and `backup_dir: build.bak` from `content/_data/config.yaml`.

*   **Warning:** Since this task appears already completed, you should verify the implementation against the acceptance criteria and ensure it's properly tested rather than re-implementing it.