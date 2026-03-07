# ============================================================
# S25 LUMIÈRE — Dockerfile Multi-Service
# Une image → 5 services via SERVICE= env var
#
# Build: docker build -t s25-command-center .
# Run core-dev:    docker run -e SERVICE=core-dev    -p 7777:7777 s25-command-center
# Run voice-relay: docker run -e SERVICE=voice-relay -p 7779:7779 s25-command-center
# Run executor:    docker run -e SERVICE=executor    -p 7780:7780 s25-command-center
# ============================================================
FROM python:3.11-slim

LABEL maintainer="Major Stef <stephaneboss>"
LABEL description="S25 Lumière — Multi-Service Command Center"
LABEL version="3.0.0"

# Install system deps
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psutil flask flask-cors websockets

# Copy full repo
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Non-root user for security
RUN useradd -m -u 1000 s25 && chown -R s25:s25 /app
USER s25

# Default: core-dev cockpit port
EXPOSE 7777 7778 7779 7780 7781

# Health check (adaptatif selon SERVICE)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7777}/health || exit 1

# Route vers le bon service selon SERVICE= env var
CMD ["sh", "entrypoint.sh"]
