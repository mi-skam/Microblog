.PHONY: help install install-dev build serve test lint format clean docker-build docker-run

# Default target
help:
	@echo "Microblog Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install      Install the package in development mode"
	@echo "  install-dev  Install with development dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  build        Build the static site"
	@echo "  serve        Start the development server"
	@echo "  test         Run the test suite"
	@echo "  lint         Run code linting with ruff"
	@echo "  format       Format code with ruff"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build Build the Docker image"
	@echo "  docker-run   Run the application in Docker"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean        Clean build artifacts and cache files"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Build and serve
build:
	microblog build

serve:
	microblog serve --reload

# Testing and quality
test:
	pytest tests/ -v

lint:
	ruff check microblog/ tests/

format:
	ruff format microblog/ tests/
	ruff check --fix microblog/ tests/

# Docker
docker-build:
	docker build -t microblog:latest .

docker-run:
	docker-compose up -d

docker-down:
	docker-compose down

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true

# Development workflow shortcuts
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make serve' to start the development server"

check: lint test
	@echo "Code quality checks passed!"

# Initialize a new blog project
init:
	microblog init
	@echo "New microblog project initialized!"

# Show project status
status:
	microblog status