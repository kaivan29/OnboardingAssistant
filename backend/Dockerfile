FROM python:3.11-slim

WORKDIR /app

# Install git for GitPython
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use shell form to allow environment variable expansion
# Cloud Run sets PORT env var, default to 8080 for local testing
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
