# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T2",
  "iteration_id": "I5",
  "iteration_goal": "Implement HTMX-enhanced interactivity, live markdown preview, image management, and build system integration with the dashboard",
  "description": "Create deployment architecture diagram showing different deployment options (full stack, hybrid, container) with infrastructure components and data flow patterns.",
  "agent_type_hint": "DiagrammingAgent",
  "inputs": "Deployment options from specification, infrastructure requirements, data flow patterns",
  "target_files": ["docs/diagrams/deployment.puml"],
  "input_files": [".codemachine/artifacts/plan/01_Plan_Overview_and_Setup.md"],
  "deliverables": "PlantUML deployment diagram showing architecture options",
  "acceptance_criteria": "Diagram shows all deployment options, infrastructure components included, data flows illustrated, scaling considerations visible",
  "dependencies": ["I4.T2"],
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
*   **File:** `docs/diagrams/component_diagram.puml`
    *   **Summary:** This file contains an existing C4 component diagram that demonstrates the PlantUML format and C4 modeling standards used in the project.
    *   **Recommendation:** You MUST follow the same PlantUML format and C4 modeling conventions as shown in this file. Use the C4_Deployment.puml include for deployment diagrams.
*   **File:** `Dockerfile`
    *   **Summary:** This file contains the container deployment configuration showing the Python 3.11 base image, application setup, and port exposure (8000).
    *   **Recommendation:** You SHOULD reference this container configuration in your deployment diagram to show the containerized deployment option accurately.
*   **File:** `docker-compose.yml`
    *   **Summary:** This file shows the development container setup with volume mounts for content, build output, templates, and static files, plus optional nginx reverse proxy configuration.
    *   **Recommendation:** You SHOULD include the volume mounting strategy and nginx reverse proxy option in your deployment diagram.
*   **File:** `microblog/server/config.py`
    *   **Summary:** This file contains comprehensive configuration management with support for different deployment environments (development vs production settings).
    *   **Recommendation:** You SHOULD illustrate how configuration differs between deployment environments in your diagram.

### Implementation Tips & Notes
*   **Tip:** I confirmed that the project follows C4 modeling standards with PlantUML. The existing component diagram uses `!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml` - you SHOULD use the corresponding C4_Deployment.puml include for consistency.
*   **Note:** The architecture documentation already contains a sample deployment diagram in PlantUML format. You SHOULD use this as a starting point but expand it to show ALL three deployment options (full stack, hybrid, container) as separate deployment scenarios.
*   **Warning:** The acceptance criteria specifically requires showing "data flow patterns" and "scaling considerations". Make sure your diagram illustrates not just static architecture but also how data flows between components and how each deployment option scales.
*   **Tip:** The existing diagrams directory contains auth_flow.puml, build_process.puml, component_diagram.puml, and database_erd.puml. Your deployment.puml should maintain the same naming convention and quality standards.
*   **Note:** The server configuration in `microblog/server/app.py` shows the application listens on port 8000 by default, with CORS and security middleware. This should be reflected in your deployment diagram.
*   **Tip:** The nginx configuration sample in the architecture documentation shows both dashboard proxying (to port 8000) and static file serving (from build directory). This hybrid approach should be prominently featured in your deployment options.