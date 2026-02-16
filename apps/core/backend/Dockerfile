# Backend Dockerfile - FastAPI with uv
#
# Builds from apps/core context (for access to session_db).
# session_db is installed as a pip package from sibling directory.
#
# Build context: apps/core
# Dockerfile location: apps/core/backend/Dockerfile

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

# Copy session_db package (with src layout)
COPY session_db /app/session_db

# Copy backend package
COPY backend/pyproject.toml /app/backend/
WORKDIR /app/backend

# Install dependencies with uv
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy backend source code
COPY backend /app/backend

# Set Python path to include session_db src
ENV PYTHONPATH=/app/backend:/app/session_db/src

# Expose port
EXPOSE 8000

# Default command
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
