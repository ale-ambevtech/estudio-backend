FROM python:3.11-slim AS base

WORKDIR /app

# Define default values without referencing undefined variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    UPLOAD_DIR=/app/uploads \
    DEBUG_DIR=/app/debug \
    MAX_FILE_SIZE=104857600 \
    CHUNK_SIZE=1048576 \
    PORT=8123 \
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

EXPOSE ${PORT}

# Use uvicorn directly
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]