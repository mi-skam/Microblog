# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY microblog/ microblog/
COPY templates/ templates/
COPY static/ static/

# Create necessary directories
RUN mkdir -p content/posts content/pages content/images content/_data build

# Install the package in development mode
RUN pip install -e .

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1000 microblog && \
    chown -R microblog:microblog /app

USER microblog

# Expose port for the web server
EXPOSE 8000

# Default command to run the application
CMD ["microblog", "serve", "--host", "0.0.0.0", "--port", "8000"]