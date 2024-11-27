FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    UPLOAD_DIR=/app/uploads \
    DEBUG_DIR=/app/debug \
    MAX_FILE_SIZE=104857600 \
    CHUNK_SIZE=1048576 \
    PATH="/home/appuser/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    linux-headers-generic \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Create non-root user
RUN useradd --create-home appuser \
    && mkdir -p ${UPLOAD_DIR} ${DEBUG_DIR} \
    && chown -R appuser:appuser /app

# Copy project files
COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

# Install Python dependencies ensuring binaries are in PATH
RUN pip install --no-cache-dir --user -r requirements.txt

# Create required directories with proper permissions
RUN mkdir -p ${UPLOAD_DIR} ${DEBUG_DIR}

EXPOSE 8000

# Use uvicorn directly
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
