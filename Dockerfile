# ================================================================
# S25 LUMIERE – Dockerfile
# Cockpit Command Center
# Build: docker build -t s25-cockpit .
# Run:   docker run -p 5000:5000 -p 5001:5001 -p 5002:5002 -p 5003:5003 --env-file .env s25-cockpit
# ================================================================
FROM python:3.11-slim

ARG BUILD_SHA=dev

LABEL maintainer="Major Stef <stephaneboss>"
LABEL description="S25 Lumiere – Command Center Cockpit"
LABEL version="2.1.0"
LABEL org.opencontainers.image.revision="${BUILD_SHA}"

# Install system deps
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl git ca-certificates && \
            rm -rf /var/lib/apt/lists/*

            # Set workdir
            WORKDIR /app
            ENV APP_BUILD_SHA="${BUILD_SHA}"
            ENV PYTHONUNBUFFERED=1
            ENV AGENTS_PATH="/app/agents"
            ENV CONFIGS_PATH="/app/configs"

            # Copy requirements first (cache layer)
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt && \
                pip install --no-cache-dir psutil flask flask-cors

                # Copy full repo
                COPY . .

                # Make scripts executable
                RUN chmod +x /app/scripts/start_cockpit_stack.sh && \
                    chmod +x /app/scripts/*.sh 2>/dev/null || true

                    # Initialize agent paths and configs
                    RUN mkdir -p /app/agents/configs && \
                        mkdir -p /app/runtime/logs && \
                            mkdir -p /app/runtime/state

                            # Non-root user for security
                            RUN useradd -m -u 1000 s25 && chown -R s25:s25 /app
                            USER s25

                            # Expose all agent ports
                            # Port 5000: ai_router (main orchestrator)
                            # Port 5001: ARKON (validator)
                            # Port 5002: MERLIN (web checker)
                            # Port 5003: COMET (health monitor)
                            EXPOSE 5000 5001 5002 5003 8080

                            # Health check - verify router availability
                            HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
                                CMD curl -f http://localhost:5000/health || exit 1

                                # Entrypoint: Initialize agents and start cockpit
                                ENTRYPOINT ["/bin/bash", "-c"]
                                CMD ["/app/scripts/start_cockpit_stack.sh"]
                                
