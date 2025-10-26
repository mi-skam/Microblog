# Microblog

A lightweight, self-hosted blogging platform that generates static HTML pages for performance while providing a dynamic HTMX-powered dashboard for content management.

## Features

- **Static-First Architecture**: Generate fast static HTML sites from markdown content
- **Dynamic Dashboard**: HTMX-enhanced management interface for content editing
- **Single-User Design**: Simple authentication without complex permission systems
- **Markdown Support**: Full markdown processing with YAML frontmatter
- **Tag-Based Organization**: Organize content with tags and generate tag pages
- **RSS Feed Generation**: Automatic RSS feed for your blog
- **Image Management**: Upload and organize images with automatic build-time copying
- **CLI Tools**: Command-line interface for build, serve, and management operations
- **Docker Support**: Containerized deployment for easy hosting
- **Live Preview**: Real-time markdown preview during content editing

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/microblog.git
cd microblog

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using Make (Recommended)

```bash
# Install with development dependencies
make install-dev

# Start the development server
make serve

# Build the static site
make build

# Run tests
make test

# Format and lint code
make format
make lint
```

### Manual Commands

```bash
# Initialize a new blog project
microblog init

# Create an admin user
microblog create-user

# Build the static site
microblog build

# Start the development server
microblog serve --reload

# Check project status
microblog status
```

## CLI Commands

The `microblog` command provides several subcommands:

- `microblog build` - Build the static site from markdown content
- `microblog serve` - Start the development server with dashboard
- `microblog create-user` - Create admin user for dashboard access
- `microblog init` - Initialize a new blog project structure
- `microblog status` - Show current project status
- `microblog --help` - Show all available commands and options

## Directory Structure

```
microblog/
├── microblog/              # Main Python package
│   ├── builder/            # Static site generation
│   ├── server/             # Web application and dashboard
│   ├── auth/               # Authentication and user management
│   ├── content/            # Content management services
│   ├── cli.py              # Click-based CLI interface
│   └── utils.py            # Shared utilities
├── templates/              # Jinja2 templates for site generation
├── static/                 # Static assets (CSS, JS, images)
├── content/                # User content directory
│   ├── posts/              # Markdown blog posts
│   ├── pages/              # Static pages
│   ├── images/             # User-uploaded images
│   └── _data/              # Configuration files
├── build/                  # Generated static site (gitignored)
├── tests/                  # Test suite
└── docs/                   # Documentation and design artifacts
```

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Frontend**: HTMX, Pico.css, Vanilla JavaScript (minimal)
- **Database**: SQLite3 (single-user authentication)
- **Template Engine**: Jinja2
- **Markdown Processing**: python-markdown + pymdown-extensions
- **Authentication**: JWT with bcrypt password hashing
- **CLI**: Click framework
- **Development**: Ruff (linting/formatting), pytest (testing)

## Docker Deployment

### Development with Docker

```bash
# Build and run with docker-compose
make docker-run

# Or manually
docker-compose up -d
```

### Production Deployment

```bash
# Build the image
docker build -t microblog:latest .

# Run the container
docker run -d -p 8000:8000 \
  -v ./content:/app/content \
  -v ./build:/app/build \
  microblog:latest
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Clean build artifacts
make clean
```

### Project Status

This is an early development version (v0.1.0). The basic project structure and CLI framework are implemented, but core functionality is still being developed.

**Current Status**:
- ✅ Project structure and packaging
- ✅ CLI framework with Click
- ✅ Docker configuration
- ✅ Development tooling setup
- 🚧 Static site generation (next iteration)
- 🚧 Dashboard web application (next iteration)
- 🚧 Authentication system (next iteration)
- 🚧 Content management (next iteration)

## Architecture

Microblog uses a hybrid static-first architecture:

1. **Static Site Generation**: Content is processed into static HTML for optimal performance
2. **Dynamic Dashboard**: HTMX-powered interface for content management
3. **Single-User Design**: Simplified authentication and user management
4. **Full Rebuild Strategy**: Complete site regeneration for consistency

## Configuration

Configuration is managed through YAML files in the `content/_data/` directory:

- `config.yaml` - Main site configuration
- Environment variables for deployment settings
- CLI options for development overrides

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/yourusername/microblog).