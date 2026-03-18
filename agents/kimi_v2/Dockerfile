FROM python:3.11-slim

# Install system deps needed for some cosmpy C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create volume mount point for persistent SQLite DB
RUN mkdir -p /data
ENV DB_PATH=/data/trades.db

# Default mode is DRY — override with S25_MODE env var
ENV S25_MODE=dry

CMD ["python", "main.py"]
