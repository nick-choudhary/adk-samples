# ============================================
# Multi-stage Dockerfile for Outbound Automation System
# Optimized for production deployment
# ============================================

# ============================================
# Stage 1: Base Python image with system dependencies
# ============================================
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Stage 2: Dependencies installation
# ============================================
FROM base AS dependencies

# Install uv for faster dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv pip install --system --no-cache-dir -e .

# ============================================
# Stage 3: Production image
# ============================================
FROM base AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY outbound_system/ ./outbound_system/
COPY lead_extraction/ ./lead_extraction/
COPY scripts/ ./scripts/
COPY pyproject.toml ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

# ============================================
# Stage 4: Development image (optional)
# ============================================
FROM dependencies AS development

WORKDIR /app

# Copy application code
COPY . .

# Install development dependencies
RUN uv pip install --system --no-cache-dir -e ".[dev]"

# Expose port
EXPOSE 8080

# Development command with auto-reload
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# ============================================
# Build instructions:
# ============================================
# Production build:
#   docker build --target production -t outbound-system:latest .
#
# Development build:
#   docker build --target development -t outbound-system:dev .
#
# Run production:
#   docker run -p 8080:8080 --env-file .env outbound-system:latest
#
# Run development:
#   docker run -p 8080:8080 -v $(pwd):/app --env-file .env outbound-system:dev
# ============================================
