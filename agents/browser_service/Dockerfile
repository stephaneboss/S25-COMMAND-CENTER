FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install flask playwright && \
    playwright install chromium && \
    playwright install-deps chromium

COPY browser_api.py .

EXPOSE 7070

CMD ["python", "browser_api.py"]
