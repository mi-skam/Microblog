# MicroBlog Specification (Updated)

## Part 1: The Essentials

### 1.0 Project Overview

**1.1 Project Name:** MicroBlog

**1.2 Project Goal:** A lightweight, self-hosted blogging platform that generates static HTML pages for performance while providing a dynamic HTMX-powered dashboard for content management.

**1.3 Target Audience:** Individual developers and writers who want full control over their blog infrastructure, prefer markdown-based workflows, and value simplicity over feature bloat.

---

### 2.0 Core Functionality & User Journeys

#### 2.1 Core Features List

- Single-user authentication
- Markdown-based post creation and editing
- Static site generation (full rebuild)
- HTMX-powered dashboard for CRUD operations
- Live markdown preview
- Tag-based organization
- RSS feed generation
- Filesystem-based image storage

#### 2.2 User Journeys

**Authentication:**
- User enters credentials → app **MUST** validate against stored hash → set httpOnly cookie with JWT → redirect to dashboard OR show error message
- User without valid session accesses dashboard → app **MUST** redirect to login page

**Post Creation:**
- User clicks "New Post" → app **MUST** show empty editor form with markdown textarea and metadata fields
- User types markdown → app **SHOULD** show live preview after 500ms delay without page refresh
- User adds image → user **MUST** upload to `content/images/` → reference in markdown as `![alt](../images/filename.jpg)`
- User clicks "Save Draft" → app **MUST** save markdown file with `draft: true` frontmatter → show success notification
- User clicks "Publish" → app **MUST** save markdown file with `draft: false` → trigger full site rebuild → show success notification with progress

**Post Management:**
- User views post list → app **MUST** show all posts with title, date, status (draft/published), and action buttons
- User clicks "Delete" on post → app **MUST** show confirmation dialog → YES removes file and triggers rebuild, NO cancels
- User clicks "Edit" on post → app **MUST** load post content into editor → allow modifications → save updates markdown file

**Site Building:**
- User clicks "Rebuild Site" → app **MUST** parse all markdown files → render through templates → copy images to build directory → generate static HTML in build directory → show completion status
- Automatic rebuild after publish → app **MUST** trigger full build process in background → update dashboard status
- Build process → app **MUST** preserve previous build in `build.bak/` until new build completes successfully

**Configuration Management (Dev):**
- Config file changes → app **SHOULD** detect change via file watcher → reload configuration → log reload event
- Config file invalid → app **MUST** log error and keep previous valid config

**Configuration Management (Prod):**
- Config file changes → app **MUST** require manual server restart to apply changes

**Content Viewing:**
- Visitor accesses blog URL → web server **MUST** serve static HTML files from build directory
- Visitor clicks post link → web server **MUST** serve individual post HTML page
- Visitor requests image → web server **MUST** serve from `build/images/` directory

---

### 3.0 Data Models

#### User
- `id` (REQUIRED, integer, primary key, auto-increment)
- `username` (REQUIRED, string, 3-50 chars, unique, alphanumeric + underscore)
- `email` (REQUIRED, string, valid email format, unique)
- `password_hash` (REQUIRED, string, bcrypt hashed)
- `role` (REQUIRED, fixed='admin')
- `created_at` (REQUIRED, timestamp, auto-set)

**Note:** Role field included for future extensibility but enforced as 'admin' in v1.0

#### Post (Markdown File)
- `title` (REQUIRED, string, 1-200 chars)
- `date` (REQUIRED, date, YYYY-MM-DD format)
- `slug` (OPTIONAL, string, auto-generated from title if missing, URL-safe)
- `tags` (OPTIONAL, array of strings)
- `draft` (REQUIRED, boolean, default=false)
- `description` (OPTIONAL, string, 1-300 chars, for meta tags)
- `content` (REQUIRED, markdown text)

#### Config (YAML File)
- `site.title` (REQUIRED, string)
- `site.url` (REQUIRED, string, valid URL)
- `site.author` (REQUIRED, string)
- `site.description` (OPTIONAL, string)
- `build.output_dir` (REQUIRED, string, default='build')
- `build.backup_dir` (REQUIRED, string, default='build.bak')
- `build.posts_per_page` (REQUIRED, integer, default=10)
- `server.host` (REQUIRED, string, default='127.0.0.1')
- `server.port` (REQUIRED, integer, 1024-65535)
- `server.hot_reload` (REQUIRED, boolean, default=false, dev-only)
- `auth.jwt_secret` (REQUIRED, string, min 32 chars)
- `auth.session_expires` (REQUIRED, integer, seconds, default=7200)

#### Session (JWT in httpOnly Cookie)
- `token` (REQUIRED, string, JWT)
- `user_id` (REQUIRED, integer, embedded in JWT)
- `expires_at` (REQUIRED, timestamp, embedded in JWT)

**Note:** No session table needed; JWT is stateless

#### Image File
- Stored in: `content/images/`
- Referenced in markdown: `![alt text](../images/filename.ext)`
- Copied to: `build/images/` during build process
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`

---

### 4.0 Essential Error Handling

**Invalid Login Credentials:**
- App **MUST** show "Invalid username or password" message without revealing which is incorrect
- App **MUST** log failed attempts
- App **SHOULD** implement rate limiting after 5 failed attempts

**Build Process Failure:**
- App **MUST** log detailed error to server logs
- App **MUST** show user-friendly error message in dashboard: "Build failed. Check logs for details."
- App **MUST** restore previous build from backup (`build.bak/`)
- App **MUST NOT** delete working build until new build succeeds

**Invalid Markdown Syntax:**
- App **SHOULD** render malformed markdown as-is without crashing
- App **MUST** escape HTML tags by default to prevent XSS

**Missing Required Fields:**
- App **MUST** highlight missing fields in red
- App **MUST** show validation message: "This field is required"
- App **MUST NOT** submit form until validation passes

**File System Errors:**
- App **MUST** handle missing content directory → create it with proper structure
- App **MUST** handle missing images directory → create `content/images/`
- App **MUST** handle permission errors with message: "Cannot write to content directory. Check permissions."
- App **MUST** handle disk full error gracefully without corrupting content

**Database Unavailable:**
- App **MUST** show "Authentication unavailable. Try again later." on login page
- App **MUST** log database connection errors

**Invalid Config File:**
- App **MUST** refuse to start with detailed validation errors
- App in dev mode with hot-reload **MUST** keep previous valid config and log error

**Image Upload Issues:**
- App **MUST** validate file extension against allowed list
- App **MUST** validate file size < 10MB
- App **MUST** sanitize filename (remove special chars, prevent path traversal)

---

## Part 2: Advanced Specifications

### 5.0 Formal Project Controls & Scope

#### 5.1 Document Control
- **Version:** 1.1
- **Status:** Specification Complete
- **Date:** October 26, 2025
- **Changes from 1.0:** Open questions resolved, decisions integrated

#### 5.2 Detailed Scope

**In Scope:**
- Single-user authentication (JWT in httpOnly cookies)
- Markdown-based content authoring
- Static HTML generation with full rebuild strategy
- Filesystem-based image storage in `content/images/`
- HTMX-enhanced dashboard (no full SPA)
- Post CRUD operations
- Tag-based categorization
- RSS feed generation
- Live markdown preview
- CLI tool for build/serve/deploy/create-user
- Build backup and rollback mechanism
- Config hot-reload in development mode
- Image file management (upload, reference, copy to build)

**Out of Scope:**
- Multi-user support
- User roles beyond admin
- Incremental/partial rebuilds
- Comment system (use external service if needed)
- Media library with thumbnails/optimization
- Advanced analytics (use external service)
- Email notifications
- Social media auto-posting
- Built-in search functionality (can add client-side later)
- Theme marketplace or plugin system
- Collaborative editing
- Git integration (user handles manually)
- Content approval workflows
- Image optimization/resizing (user handles pre-upload)

#### 5.3 Glossary

| Term | Definition |
|------|------------|
| **Static Site Generator (SSG)** | Tool that converts markdown + templates into static HTML files |
| **HTMX** | Library allowing access to AJAX, CSS Transitions, WebSockets via HTML attributes |
| **Frontmatter** | YAML metadata block at top of markdown files (between `---` delimiters) |
| **Slug** | URL-friendly version of post title (e.g., "My Post" → "my-post") |
| **JWT** | JSON Web Token, used for stateless authentication |
| **httpOnly Cookie** | Cookie inaccessible to JavaScript, used for secure session management |
| **Build Directory** | Output directory containing generated static HTML (`build/`) |
| **Content Directory** | Source directory containing markdown files (`content/`) |
| **Full Rebuild** | Regenerating entire site from scratch, not just changed files |
| **Hot Reload** | Automatic application of config changes without manual restart (dev only) |

---

### 6.0 Granular & Traceable Requirements

| ID | Requirement Name | Description | Priority |
|----|------------------|-------------|----------|
| **FR-001** | Single User Authentication | System **MUST** authenticate single user with username/password against bcrypt hash | Critical |
| **FR-002** | JWT Cookie Management | System **MUST** issue JWT tokens in httpOnly cookies valid for configurable duration | Critical |
| **FR-003** | Markdown Parsing | System **MUST** parse markdown files with YAML frontmatter using `python-frontmatter` | Critical |
| **FR-004** | Full Site Rebuild | System **MUST** perform complete site regeneration on every build trigger | Critical |
| **FR-005** | Build Backup | System **MUST** backup previous build before starting new build | Critical |
| **FR-006** | Build Rollback | System **MUST** restore backup if build fails | Critical |
| **FR-007** | Image File Copy | System **MUST** copy all files from `content/images/` to `build/images/` during build | High |
| **FR-008** | Post Listing | Dashboard **MUST** display all posts with metadata in sortable table | High |
| **FR-009** | Post Creation | Dashboard **MUST** provide form to create new post with title, content, tags, draft status | High |
| **FR-010** | Post Editing | Dashboard **MUST** allow editing existing post content and metadata | High |
| **FR-011** | Post Deletion | Dashboard **MUST** allow deletion with confirmation prompt | High |
| **FR-012** | Live Preview | Dashboard **SHOULD** show rendered HTML preview while typing markdown | High |
| **FR-013** | Auto-rebuild | System **MUST** trigger rebuild after post publish/update/delete | High |
| **FR-014** | Tag Autocomplete | Dashboard **SHOULD** suggest existing tags while typing | Medium |
| **FR-015** | RSS Generation | System **MUST** generate valid RSS 2.0 feed | Medium |
| **FR-016** | Draft Posts | System **MUST** exclude draft posts from public site build | Critical |
| **FR-017** | CLI Build | System **MUST** provide CLI command: `build` | Critical |
| **FR-018** | CLI Serve | System **MUST** provide CLI command: `serve` with optional dev mode | Critical |
| **FR-019** | CLI User Creation | System **MUST** provide CLI command: `create-user` | High |
| **FR-020** | Config Hot Reload (Dev) | System **SHOULD** watch config file and reload when `server.hot_reload=true` | Medium |
| **FR-021** | Config Restart (Prod) | System **MUST** require restart for config changes when `server.hot_reload=false` | High |
| **FR-022** | Image Upload | Dashboard **SHOULD** provide image upload to `content/images/` | Medium |
| **FR-023** | Image Reference Helper | Dashboard **SHOULD** provide markdown snippet after upload | Low |

---

### 7.0 Measurable Non-Functional Requirements

| ID | Category | Requirement | Metric / Acceptance Criteria |
|----|----------|-------------|------------------------------|
| **NFR-PERF-001** | Performance | Static Page Load | Generated HTML pages **MUST** be < 100KB uncompressed (excluding images) |
| **NFR-PERF-002** | Performance | Build Time | Full site rebuild with 100 posts **MUST** complete in < 5 seconds |
| **NFR-PERF-003** | Performance | Build Time (1000 posts) | Full site rebuild with 1000 posts **SHOULD** complete in < 30 seconds |
| **NFR-PERF-004** | Performance | Dashboard Response | HTMX API endpoints **MUST** respond in < 200ms for read operations |
| **NFR-PERF-005** | Performance | Config Reload | Config file changes **MUST** be detected and applied within 2 seconds (dev mode) |
| **NFR-SEC-001** | Security | Password Storage | Passwords **MUST** be hashed with bcrypt, cost factor ≥ 12 |
| **NFR-SEC-002** | Security | JWT Expiry | JWT tokens **MUST** expire and require re-authentication |
| **NFR-SEC-003** | Security | httpOnly Cookies | JWT **MUST** be stored in httpOnly, Secure, SameSite=Strict cookies |
| **NFR-SEC-004** | Security | CSRF Protection | Dashboard POST/DELETE **MUST** validate CSRF tokens |
| **NFR-SEC-005** | Security | HTML Escaping | User-generated content **MUST** have HTML escaped by default |
| **NFR-SEC-006** | Security | Image Upload Validation | Uploaded files **MUST** validate extension and size (< 10MB) |
| **NFR-SEC-007** | Security | Path Traversal Prevention | Image filenames **MUST** be sanitized to prevent directory traversal |
| **NFR-USE-001** | Usability | Dashboard Feedback | All user actions **MUST** show visual feedback within 100ms |
| **NFR-USE-002** | Usability | Build Progress | Rebuild **MUST** show progress indicator during operation |
| **NFR-REL-001** | Reliability | Build Idempotency | Running build twice **MUST** produce identical output |
| **NFR-REL-002** | Reliability | Build Atomicity | Failed build **MUST NOT** leave site in broken state |
| **NFR-MAINT-001** | Maintainability | Code Style | Code **MUST** follow PEP 8 and pass `ruff` linting |
| **NFR-MAINT-002** | Maintainability | Type Hints | All functions **SHOULD** include type hints |
| **NFR-PORT-001** | Portability | Python Version | System **MUST** work on Python 3.10+ |
| **NFR-DEPLOY-001** | Deployment | Static Output | Build directory **MUST** be servable by any static file server (nginx, Apache, Caddy) |
| **NFR-DEPLOY-002** | Deployment | Directory Structure | System **MUST** create required directories if missing on first run |

---

### 8.0 Technical & Architectural Constraints

#### 8.1 Technology Stack

**Backend:**
- **Framework:** FastAPI 0.100+
- **Template Engine:** Jinja2
- **Markdown:** `markdown` library with `pymdown-extensions`
- **Frontmatter:** `python-frontmatter`
- **Auth:** `python-jose[cryptography]` + `passlib[bcrypt]`
- **Database:** SQLite3 (Python stdlib) for single user record
- **CLI:** `click` or `typer`
- **File Watching:** `watchfiles` (for dev mode config hot-reload)

**Frontend:**
- **HTMX:** Latest stable (vendored locally in `static/js/`)
- **CSS:** Vanilla CSS or Pico.css (< 10KB)
- **No JavaScript framework** (React, Vue, etc.) for dashboard

**Development:**
- **Python:** 3.10 minimum, 3.12 recommended
- **Package Manager:** uv (preferred) or Poetry
- **Linter:** Ruff
- **Formatter:** Ruff format

#### 8.2 Architectural Principles

- **Separation of Concerns:** Builder module independent of server module
- **Static-First:** Public site **MUST** be servable without Python runtime
- **Progressive Enhancement:** Dashboard **MUST** work without HTMX (graceful degradation)
- **Single Responsibility:** Each module handles one domain (auth, builder, server)
- **Filesystem as Source of Truth:** Markdown files are canonical source for content
- **Full Rebuild Philosophy:** Simplicity over optimization; rebuild everything every time
- **Stateless Authentication:** JWT in cookies eliminates need for session storage
- **Fail-Safe Operations:** Always backup before destructive operations

#### 8.3 Deployment Environment

**Development:**
- Local Python environment (venv or similar)
- `microblog serve --dev` starts server with hot-reload enabled
- `microblog build --watch` rebuilds on file changes

**Production Options:**

**Option 1 - Full Stack (Dashboard + Static):**
```
nginx (443) 
  ├─> /dashboard/* → FastAPI (127.0.0.1:8000)
  └─> /* → static files (build/)
```

**Option 2 - Static Only:**
```
Build locally:
  microblog build
  
Deploy build/ to:
  - Cloudflare Pages
  - Netlify
  - nginx document root
  - Any static host
  
Dashboard access: Local only
```

**Option 3 - Hybrid (Recommended):**
```
Edit locally with dashboard:
  microblog serve --dev
  
Deploy static output:
  microblog build
  rsync build/ user@server:/var/www/blog/
```

**File Structure:**
```
/opt/microblog/
  content/
    posts/
      2025-10-26-example.md
    pages/
      about.md
    images/
      photo.jpg
    _data/
      config.yaml
  build/              # Generated site
  build.bak/          # Previous build
  microblog.db        # Single user record
  .venv/              # Python environment
```

**Systemd Service (if running dashboard in production):**
```ini
[Unit]
Description=MicroBlog Dashboard
After=network.target

[Service]
Type=simple
User=microblog
WorkingDirectory=/opt/microblog
Environment="PATH=/opt/microblog/.venv/bin"
ExecStart=/opt/microblog/.venv/bin/microblog serve --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### 9.0 Assumptions, Dependencies & Risks

#### 9.1 Assumptions

- User has basic familiarity with markdown syntax
- Content volume will not exceed 10,000 posts (performance tested up to 1000)
- User will manually back up content directory via git or other means
- Filesystem has sufficient permissions for read/write operations
- Images are pre-optimized before upload (no automatic compression)
- Single user eliminates need for complex permission system
- Full rebuild strategy is acceptable for initial scope
- Network latency to server is < 100ms (for HTMX responsiveness)
- User runs dashboard on trusted network (localhost or VPN)

#### 9.2 Dependencies

**Runtime Dependencies:**
- Python 3.10+ available on system
- Write permissions to content, build, and build.bak directories
- SQLite3 (bundled with Python)
- Disk space for build backups (2x build directory size minimum)

**External Services:**
- None required for core functionality
- Optional: CDN for static file serving in production
- Optional: Git for content version control

**Python Package Dependencies:**
- fastapi
- uvicorn
- jinja2
- markdown
- pymdown-extensions
- python-frontmatter
- python-jose[cryptography]
- passlib[bcrypt]
- click or typer
- watchfiles (dev mode only)
- pyyaml

#### 9.3 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Build process corruption leaves site unusable | High | Low | **RESOLVED:** Backup mechanism preserves previous build |
| Large media files exceed disk space | High | Medium | Document image optimization, warn on large uploads |
| Config hot-reload causes server instability | Medium | Low | Disable in production by default, test thoroughly in dev |
| Filesystem limitations with 10,000+ images | Medium | Low | Document directory structure best practices, consider subdirs |
| JWT secret exposure compromises all sessions | High | Low | Require 32+ char secret, document rotation procedure |
| Full rebuild too slow for large sites | High | Low | Document 30s limit for 1000 posts, plan incremental option for future |
| Single user limitation frustrates team workflows | Medium | Medium | Document clearly in README, plan multi-user for v2.0 |
| Image upload without compression fills disk | Medium | High | **RESOLVED:** 10MB limit per file, document pre-optimization |

---

### 10.0 Implementation Phases

**Phase 1: Core Builder (MVP)**
- ✓ Directory structure creation
- ✓ Markdown parsing with frontmatter
- ✓ Jinja2 template rendering
- ✓ Image file copying from content/images/ to build/images/
- ✓ CLI: `build` command
- ✓ Static file output with proper structure

**Phase 2: Build Safety**
- ✓ Build backup mechanism (build → build.bak)
- ✓ Atomic build (complete or rollback)
- ✓ Build status reporting
- ✓ Error logging

**Phase 3: Authentication**
- ✓ User model + SQLite (single record)
- ✓ JWT token generation
- ✓ httpOnly cookie management
- ✓ Login/logout endpoints
- ✓ Auth middleware
- ✓ CLI: `create-user` command

**Phase 4: Dashboard Foundation**
- ✓ FastAPI routes for dashboard
- ✓ Post list view (server-rendered)
- ✓ Basic CRUD without HTMX
- ✓ Form validation

**Phase 5: HTMX Integration**
- ✓ Live markdown preview
- ✓ Inline delete with confirmation
- ✓ Draft/publish toggle
- ✓ Auto-rebuild trigger with progress

**Phase 6: Image Management**
- ✓ Image upload endpoint
- ✓ File validation (extension, size)
- ✓ Filename sanitization
- ✓ Markdown snippet generation
- ✓ Optional: Image list view in dashboard

**Phase 7: Configuration**
- ✓ YAML config parsing
- ✓ Config validation on startup
- ✓ File watcher for hot-reload (dev mode)
- ✓ CLI: `serve --dev` flag

**Phase 8: Polish**
- ✓ Tag autocomplete
- ✓ RSS feed generation
- ✓ CSRF protection
- ✓ Rate limiting on login
- ✓ Comprehensive error messages
- ✓ CLI help documentation

---

### 11.0 File Structure Reference

```
microblog/
├── microblog/
│   ├── __init__.py
│   ├── builder/
│   │   ├── __init__.py
│   │   ├── generator.py      # Main build orchestration
│   │   ├── markdown.py       # Markdown processing
│   │   ├── templates.py      # Template rendering
│   │   └── assets.py         # Image/static file copying
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py           # FastAPI app initialization
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py # Dashboard views
│   │   │   ├── api.py       # HTMX API endpoints
│   │   │   └── auth.py      # Login/logout
│   │   ├── middleware.py    # Auth middleware
│   │   └── config.py        # Config hot-reload watcher
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py        # User model (SQLite)
│   │   └── auth.py          # JWT + password hashing
│   └── cli.py               # Click/Typer CLI interface
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── post.html
│   ├── archive.html
│   ├── tag.html
│   └── dashboard/
│       ├── layout.html
│       ├── login.html
│       ├── posts_list.html
│       ├── post_edit.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── htmx.min.js
├── content/                 # User's content (git-tracked)
│   ├── posts/
│   ├── pages/
│   ├── images/
│   └── _data/
│       └── config.yaml
├── build/                   # Generated site (gitignored)
├── build.bak/               # Backup (gitignored)
├── pyproject.toml
├── README.md
└── Makefile                 # Optional: make serve, make build
```

---

### 12.0 Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-26 | Filesystem for images | Simplicity; no external dependencies; fits static-first philosophy |
| 2025-10-26 | Single-user only | Reduces complexity; user requested; sufficient for target audience |
| 2025-10-26 | Full rebuild always | Simpler implementation; < 5s for 100 posts acceptable; can optimize later |
| 2025-10-26 | JWT in httpOnly cookies | HTMX-compatible; more secure than localStorage; stateless |
| 2025-10-26 | Config hot-reload (dev), restart (prod) | Best of both worlds; safety in prod, convenience in dev |

---

**End of Specification**