# MicroBlog Deployment Guide

This guide covers deployment of MicroBlog in production environments, including full stack deployment, hybrid deployment, and containerized deployment options.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Full Stack Deployment](#full-stack-deployment)
4. [Hybrid Deployment](#hybrid-deployment)
5. [Container Deployment](#container-deployment)
6. [Configuration](#configuration)
7. [Security](#security)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 22.04 LTS (recommended) or compatible Linux distribution
- **Python**: 3.11 or higher
- **Memory**: Minimum 1GB RAM (2GB+ recommended)
- **Storage**: 10GB available space (more for content and backups)
- **Network**: Public IP address with ports 80/443 accessible

### Required Software

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install web server and SSL tools
sudo apt install -y nginx certbot python3-certbot-nginx

# Install database tools (for SQLite management)
sudo apt install -y sqlite3

# Install system utilities
sudo apt install -y git curl wget htop unzip
```

### User Setup

Create a dedicated user for running MicroBlog:

```bash
# Create microblog user
sudo adduser --system --group --home /opt/microblog microblog

# Set up directory structure
sudo mkdir -p /opt/microblog
sudo chown microblog:microblog /opt/microblog
```

## Deployment Options

MicroBlog supports three main deployment architectures:

### 1. Full Stack Deployment
- **Best for**: Small to medium blogs, full control needed
- **Components**: nginx + FastAPI dashboard + static files
- **Scaling**: Vertical scaling only
- **Complexity**: Medium

### 2. Hybrid Deployment
- **Best for**: High-traffic static sites, cost optimization
- **Components**: Local dashboard + CDN static hosting
- **Scaling**: Infinite (CDN-based)
- **Complexity**: Low to Medium

### 3. Container Deployment
- **Best for**: Enterprise environments, high availability
- **Components**: Docker containers + orchestration
- **Scaling**: Horizontal auto-scaling
- **Complexity**: High

## Full Stack Deployment

This is the recommended deployment for most use cases, providing a complete self-hosted solution.

### Step 1: Application Setup

```bash
# Switch to microblog user
sudo su - microblog

# Clone the repository
cd /opt/microblog
git clone https://github.com/your-org/microblog.git .

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the application
pip install -e .
```

### Step 2: Configuration

Create the production configuration file:

```bash
# Create configuration directory
mkdir -p /opt/microblog/content/_data

# Create main configuration file
cat > /opt/microblog/config.yaml << EOF
# Production configuration for MicroBlog
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

site:
  name: "Your Blog Name"
  description: "Your blog description"
  url: "https://blog.example.com"
  author:
    name: "Your Name"
    email: "your@email.com"

build:
  output_dir: "build"

security:
  secret_key: "$(openssl rand -hex 32)"

# Add other configuration as needed
EOF

# Set proper permissions
chmod 600 /opt/microblog/config.yaml
```

### Step 3: Database Initialization

```bash
# Initialize the database and create admin user
microblog create-user --username admin --email admin@example.com

# Test the application
microblog serve --config /opt/microblog/config.yaml
```

### Step 4: Systemd Service Setup

```bash
# Copy systemd service file
sudo cp /opt/microblog/systemd/microblog.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable microblog
sudo systemctl start microblog

# Check service status
sudo systemctl status microblog
```

### Step 5: Nginx Configuration

```bash
# Copy nginx configuration
sudo cp /opt/microblog/nginx/microblog.conf /etc/nginx/sites-available/

# Update server_name in the configuration
sudo sed -i 's/blog.example.com/your-domain.com/g' /etc/nginx/sites-available/microblog.conf

# Enable the site
sudo ln -s /etc/nginx/sites-available/microblog.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 6: SSL Certificate Setup

```bash
# Obtain SSL certificate with Certbot
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### Step 7: Initial Build and Deployment

```bash
# Switch back to microblog user
sudo su - microblog
cd /opt/microblog

# Build the static site
source .venv/bin/activate
microblog build --config /opt/microblog/config.yaml

# Test the deployment
curl -f http://localhost:8000/health
```

## Hybrid Deployment

For high-performance static hosting with local content management.

### Local Setup

Set up MicroBlog locally for content management:

```bash
# Install MicroBlog locally
git clone https://github.com/your-org/microblog.git
cd microblog
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Start local dashboard
microblog serve --reload
```

### Static Hosting

Deploy the generated static files to your preferred hosting platform:

#### Netlify Deployment

```bash
# Build the site
microblog build

# Install Netlify CLI
npm install -g netlify-cli

# Deploy to Netlify
netlify deploy --prod --dir=build
```

#### Cloudflare Pages

```bash
# Build the site
microblog build

# Upload to Cloudflare Pages (via dashboard or CLI)
# Files from the build/ directory
```

#### Custom Static Host

```bash
# Build and sync to server
microblog build
rsync -avz --delete build/ user@server:/var/www/html/
```

## Container Deployment

Deploy using Docker and Docker Compose for scalability and consistency.

### Single Container Deployment

```bash
# Build the Docker image
docker build -t microblog:latest .

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  microblog:
    build: .
    image: microblog:latest
    container_name: microblog_app
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./content:/app/content
      - ./build:/app/build
      - ./config.yaml:/app/config.yaml:ro
      - microblog_data:/app/data
    environment:
      - MICROBLOG_ENV=production
      - MICROBLOG_DEBUG=false
    command: ["microblog", "serve", "--config", "/app/config.yaml", "--host", "0.0.0.0"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: microblog_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./build:/usr/share/nginx/html:ro
      - certbot_certs:/etc/letsencrypt
    depends_on:
      - microblog

volumes:
  microblog_data:
  certbot_certs:
```

### Kubernetes Deployment

For enterprise Kubernetes deployments, see the `k8s/` directory for manifests.

## Configuration

### Environment-Specific Settings

#### Development Configuration

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

build:
  watch: true

logging:
  level: "DEBUG"
```

#### Production Configuration

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

security:
  secret_key: "${SECRET_KEY}"
  csrf_protection: true

logging:
  level: "INFO"
  format: "json"

performance:
  cache_enabled: true
  compression: true
```

### Configuration Management

Use environment variables for sensitive configuration:

```bash
# Set environment variables
export MICROBLOG_SECRET_KEY="your-secret-key"
export MICROBLOG_DATABASE_URL="sqlite:///microblog.db"

# Reference in config.yaml
security:
  secret_key: "${MICROBLOG_SECRET_KEY}"
```

## Security

### SSL/TLS Configuration

Ensure strong SSL configuration in nginx:

```nginx
# Modern TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;

# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options DENY always;
```

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Application Security

- Use strong secret keys
- Enable CSRF protection
- Implement rate limiting
- Regular security updates
- Monitor access logs

## Monitoring and Maintenance

### Log Management

View application logs:

```bash
# Systemd service logs
sudo journalctl -u microblog -f

# Nginx access logs
sudo tail -f /var/log/nginx/microblog_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/microblog_error.log
```

### Backup Strategy

Use the included backup script:

```bash
# Create backup
sudo /opt/microblog/scripts/backup.sh --compress --remote

# Schedule regular backups
sudo crontab -e
# Add: 0 2 * * * /opt/microblog/scripts/backup.sh --compress >/dev/null 2>&1
```

### Deployment Automation

Use the deployment script for updates:

```bash
# Deploy latest version
sudo /opt/microblog/scripts/deploy.sh --backup

# Deploy without backup
sudo /opt/microblog/scripts/deploy.sh --no-backup

# Deploy with custom config
sudo /opt/microblog/scripts/deploy.sh --config /path/to/config.yaml
```

### Health Monitoring

Set up monitoring endpoints:

```bash
# Check application health
curl -f http://localhost:8000/health

# Check nginx status
sudo systemctl status nginx

# Check service status
sudo systemctl status microblog
```

### Performance Monitoring

Monitor system resources:

```bash
# Monitor system resources
htop

# Monitor disk usage
df -h

# Monitor nginx connections
sudo ss -tulpn | grep nginx
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check service status and logs
sudo systemctl status microblog
sudo journalctl -u microblog -n 50

# Common fixes:
# 1. Check configuration file syntax
microblog build --config /opt/microblog/config.yaml --verbose

# 2. Check file permissions
sudo chown -R microblog:microblog /opt/microblog

# 3. Check virtual environment
sudo su - microblog
source .venv/bin/activate
which microblog
```

#### Nginx Configuration Issues

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Common fixes:
# 1. Check domain name in configuration
# 2. Verify SSL certificate paths
# 3. Check file permissions for static files
```

#### SSL Certificate Problems

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

#### Database Issues

```bash
# Check database file permissions
ls -la /opt/microblog/microblog.db

# Backup and recreate database
cp microblog.db microblog.db.backup
rm microblog.db
microblog create-user --username admin --email admin@example.com
```

#### Performance Issues

```bash
# Check system resources
free -h
df -h
iostat 1

# Check application logs for errors
sudo journalctl -u microblog -p err

# Monitor nginx connections
sudo netstat -an | grep :80 | wc -l
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Temporary debug mode
sudo systemctl stop microblog
sudo su - microblog
cd /opt/microblog
source .venv/bin/activate
microblog serve --config config.yaml --verbose

# Check for errors in output
```

### Log Analysis

```bash
# Analyze nginx access logs
sudo tail -1000 /var/log/nginx/microblog_access.log | \
  awk '{print $1}' | sort | uniq -c | sort -nr | head -10

# Check for failed requests
sudo grep "HTTP/1.1\" [45]" /var/log/nginx/microblog_access.log

# Monitor real-time access
sudo tail -f /var/log/nginx/microblog_access.log | grep -v "\.css\|\.js\|\.png\|\.jpg"
```

## Backup and Recovery

### Automated Backups

The backup script supports various options:

```bash
# Daily backup with compression
/opt/microblog/scripts/backup.sh --compress

# Weekly backup with remote upload
/opt/microblog/scripts/backup.sh --compress --remote

# Custom retention period
/opt/microblog/scripts/backup.sh --retention 7
```

### Recovery Procedures

```bash
# List available backups
ls -la /opt/microblog/backups/

# Restore from backup
cd /opt/microblog
sudo systemctl stop microblog
sudo cp -r backups/backup_YYYYMMDD_HHMMSS/* .
sudo chown -R microblog:microblog .
sudo systemctl start microblog
```

## Scaling and Optimization

### Horizontal Scaling

For high-traffic deployments:

1. Use a load balancer (nginx, HAProxy)
2. Deploy multiple application instances
3. Use shared storage for content
4. Implement session persistence

### Caching Strategy

1. Static file caching (nginx)
2. Application-level caching
3. CDN for global distribution
4. Database query optimization

### Performance Tuning

```bash
# Optimize nginx worker processes
worker_processes auto;
worker_connections 1024;

# Enable gzip compression
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript;

# Optimize systemd service
LimitNOFILE=65536
LimitNPROC=4096
```

This deployment guide provides comprehensive instructions for deploying MicroBlog in various environments. Choose the deployment option that best fits your requirements and infrastructure constraints.