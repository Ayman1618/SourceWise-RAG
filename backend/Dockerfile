# SourceWise RAG - Backend Production Dockerfile
# Python 3.11+ compatible (Python 3.12-slim base)
FROM python:3.12-slim

# Set environment variables for Python in container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    APP_ENV=production \
    BACKEND_HOST=0.0.0.0

WORKDIR /app

# Install system dependencies (curl and certificates for healthcheck and HTTPS requests)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy backend application source code
COPY . .

# Create non-privileged user for security compliance
RUN adduser --disabled-password --gecos "" --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose default backend port
EXPOSE 8000

# Built-in health check using Python standard library
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health')" || exit 1

# Start Uvicorn server dynamically binding to 0.0.0.0 and platform PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
