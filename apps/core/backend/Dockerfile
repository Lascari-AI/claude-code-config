# Backend Dockerfile - FastAPI with uv and hot reload
#
# Development image optimized for:
# - Fast rebuilds with uv
# - Hot reload via uvicorn --reload
# - Source mounted as volume

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy pyproject.toml and session_db for dependency resolution
COPY pyproject.toml .
COPY session_db/pyproject.toml session_db/pyproject.toml
COPY session_db/session_db session_db/session_db

# Install dependencies with uv
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy backend code
COPY backend backend

# Set Python path to include app directory
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
