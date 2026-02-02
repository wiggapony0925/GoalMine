# =============================================================================
# GoalMine AI - Production Dockerfile
# World Cup 2026 Betting Intelligence Engine
# =============================================================================

# Stage 1: Builder (for dependency compilation)
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Production Image (Minimal)
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user for security (optional but recommended)
# RUN useradd -m goalmine && chown -R goalmine:goalmine /app
# USER goalmine

# Expose the port
EXPOSE 8000

# Health check (optional but useful for orchestrators)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application with Gunicorn for production
# Using async workers for your async Flask routes
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "gevent", "--timeout", "120", "app:app"]
