# ============================================================
# S25 LUMIÈRE — Dockerfile
# Cockpit Command Center
# Build: docker build -t s25-cockpit .
# Run:   docker run -p 7777:7777 --env-file .env s25-cockpit
# ============================================================
FROM python:3.11-slim

ARG BUILD_SHA=dev

LABEL maintainer="Major Stef <stephaneboss>"
LABEL description="S25 Lumière — Command Center Cockpit"
LABEL version="2.0.0"
LABEL org.opencontainers.image.revision="${BUILD_SHA}"

# Install system deps
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app
ENV APP_BUILD_SHA="${BUILD_SHA}"

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psutil flask flask-cors

# Copy full repo
COPY . .

# Non-root user for security
RUN useradd -m -u 1000 s25 && chown -R s25:s25 /app
USER s25

# Expose cockpit port
EXPOSE 7777

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7777/api/version || exit 1

# Start cockpit as a package module so absolute imports like
# `from agents...` resolve correctly in the container.
CMD ["python", "-m", "agents.cockpit_lumiere"]
