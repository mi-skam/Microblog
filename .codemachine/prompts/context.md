# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I6.T3",
  "iteration_id": "I6",
  "iteration_goal": "Implement production features, security hardening, deployment support, comprehensive documentation, and final system testing",
  "description": "Create deployment documentation and scripts including Docker configuration, systemd service files, nginx configuration, and automated deployment scripts.",
  "agent_type_hint": "DocumentationAgent",
  "inputs": "Deployment requirements, infrastructure patterns, automation needs",
  "target_files": ["scripts/deploy.sh", "scripts/backup.sh", "docs/deployment.md", "systemd/microblog.service", "nginx/microblog.conf"],
  "input_files": ["Dockerfile", "docker-compose.yml", "docs/diagrams/deployment.puml"],
  "deliverables": "Deployment scripts, service configurations, infrastructure documentation, automation tools",
  "acceptance_criteria": "Deployment scripts work correctly, service files are valid, nginx configuration functional, documentation is comprehensive",
  "dependencies": ["I5.T2"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: deployment-view (from 05_Operational_Architecture.md)

```markdown
### 3.9. Deployment View

**Target Environment:**

**Primary Deployment Options:**
1. **Development Environment**: Local workstation with hot-reload capabilities
2. **Self-Hosted VPS**: Linux server with manual deployment and management
3. **Hybrid Deployment**: Local dashboard with static output deployed to CDN
4. **Container Deployment**: Docker-based deployment for consistency

**Deployment Strategy:**

**Option 1: Full Stack Deployment (Recommended for Dynamic Management)**
```
Internet → nginx/Caddy (443) → FastAPI Dashboard (8000)
                           ↓
                    Static Files (build/)
```

**Option 2: Hybrid Deployment (Recommended for Performance)**
```
Local: MicroBlog Dashboard (development/management)
   ↓ (build + rsync/deploy)
Remote: Static File Server (production/public)
```

**Option 3: Container Deployment**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["microblog", "serve", "--host", "0.0.0.0"]
```
```

### Context: deployment-diagram (from 05_Operational_Architecture.md)

```markdown
**(Optional) Deployment Diagram (PlantUML):**
```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Deployment.puml

deploymentNode("Production Server", "Ubuntu 22.04 LTS", "VPS") {
    deploymentNode("Reverse Proxy", "nginx 1.18", "Web Server") {
        artifact("SSL Certificate", "Let's Encrypt")
        artifact("Static Files", "build/")
    }

    deploymentNode("Application Runtime", "Python 3.12", "Virtual Environment") {
        node("MicroBlog Dashboard", "FastAPI + Uvicorn", "Port 8000") {
            artifact("Dashboard App", "Python Application")
            artifact("CLI Tools", "Click Commands")
        }
    }

    deploymentNode("Data Storage", "File System", "Local Storage") {
        node("Content Directory", "content/") {
            artifact("Markdown Posts", "posts/")
            artifact("Images", "images/")
            artifact("Configuration", "_data/config.yaml")
        }
        node("Database", "SQLite") {
            artifact("User Data", "microblog.db")
        }
        node("Build Output", "build/") {
            artifact("Static HTML", "Generated Site")
        }
    }
}

deploymentNode("CDN/Static Hosting", "Optional", "Global Distribution") {
    node("Cloudflare Pages", "Static Hosting") {
        artifact("Deployed Site", "Synced from build/")
    }
}

node("Content Author", "Local Machine") {
    artifact("SSH/SFTP", "File Transfer")
    artifact("Git Repository", "Version Control")
}

@enduml
```
```

### Context: configuration-management (from 05_Operational_Architecture.md)

```markdown
**Configuration Management:**

**Environment-Specific Configurations:**
```yaml
# Development configuration
server:
  host: "127.0.0.1"
  port: 8000
  hot_reload: true
  debug: true

# Production configuration
server:
  host: "0.0.0.0"
  port: 8000
  hot_reload: false
  debug: false
```

**Deployment Scripts:**
```bash
#!/bin/bash
# Production deployment script
set -e

echo "Deploying MicroBlog..."
cd /opt/microblog

# Backup current installation
cp -r build build.backup.$(date +%Y%m%d_%H%M%S)

# Update application code
git pull origin main

# Install dependencies
.venv/bin/pip install -r requirements.txt

# Run migrations if needed
.venv/bin/microblog upgrade-db

# Rebuild site
.venv/bin/microblog build

# Restart services
sudo systemctl restart microblog
sudo systemctl restart nginx

echo "Deployment completed successfully"
```

**Service Configuration:**
```ini
# /etc/systemd/system/microblog.service
[Unit]
Description=MicroBlog Dashboard Service
After=network.target

[Service]
Type=simple
User=microblog
Group=microblog
WorkingDirectory=/opt/microblog
Environment=PATH=/opt/microblog/.venv/bin
ExecStart=/opt/microblog/.venv/bin/microblog serve --config /opt/microblog/config.yaml
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name blog.example.com;

    ssl_certificate /etc/letsencrypt/live/blog.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/blog.example.com/privkey.pem;

    # Dashboard routes
    location /dashboard {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static blog content
    location / {
        root /opt/microblog/build;
        try_files $uri $uri/ =404;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
```
```

### Context: task-i5-t2 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.2:**
    *   **Task ID:** `I5.T2`
    *   **Description:** Create deployment architecture diagram showing different deployment options (full stack, hybrid, container) with infrastructure components and data flow patterns.
    *   **Agent Type Hint:** `DiagrammingAgent`
    *   **Inputs:** Deployment options from specification, infrastructure requirements, data flow patterns
    *   **Input Files:** [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"]
    *   **Target Files:** ["docs/diagrams/deployment.puml"]
    *   **Deliverables:** PlantUML deployment diagram showing architecture options
    *   **Acceptance Criteria:** Diagram shows all deployment options, infrastructure components included, data flows illustrated, scaling considerations visible
    *   **Dependencies:** `I4.T2`
    *   **Parallelizable:** Yes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `Dockerfile`
    *   **Summary:** Contains a well-structured Docker configuration using Python 3.11-slim with proper security practices (non-root user, optimized caching).
    *   **Recommendation:** You MUST use this as the foundation for any Docker-related deployment documentation. The file already includes best practices like multi-stage caching and security considerations.

*   **File:** `docker-compose.yml`
    *   **Summary:** Provides a development-focused compose configuration with volume mounts and environment settings.
    *   **Recommendation:** You SHOULD reference this for development deployment patterns, but you'll need to create production-oriented configurations.

*   **File:** `docs/diagrams/deployment.puml`
    *   **Summary:** Comprehensive PlantUML deployment diagram showing all three deployment options (full stack, hybrid, container) with detailed infrastructure components.
    *   **Recommendation:** This diagram is already complete and should be referenced in your deployment documentation as the visual guide for deployment architecture.

*   **File:** `microblog/cli.py`
    *   **Summary:** Contains comprehensive CLI interface with serve command that supports production configuration via --config parameter and host/port overrides.
    *   **Recommendation:** You MUST reference the CLI serve command in your systemd service file and deployment scripts. The serve command already supports production mode without --reload.

*   **File:** `Makefile`
    *   **Summary:** Provides development shortcuts including docker-build and docker-run commands, plus other useful development tools.
    *   **Recommendation:** You SHOULD reference or enhance the Makefile patterns for deployment automation, especially the Docker-related commands.

### Implementation Tips & Notes

*   **Tip:** The scripts/ directory is currently empty, so you need to create all deployment and backup scripts from scratch.
*   **Note:** The CLI already supports production configuration via `microblog serve --config /path/to/config.yaml`, which is perfect for systemd service integration.
*   **Warning:** The current Dockerfile uses Python 3.11-slim but the architecture docs reference Python 3.12. You should stick with 3.11 to match the existing, working Dockerfile.
*   **Tip:** The existing docker-compose.yml includes commented nginx configuration that you can use as a starting point for your nginx configuration files.
*   **Note:** The application already includes comprehensive logging and monitoring (from I6.T1), so your deployment scripts should reference these for health checking.
*   **Warning:** You need to create a systemd/ directory since it doesn't exist yet, and the target files expect systemd service files there.
*   **Tip:** The Makefile already includes docker-build and docker-run targets that you can reference in your deployment documentation.