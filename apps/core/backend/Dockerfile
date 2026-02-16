# Backend Dockerfile - FastAPI with uv
#
# Builds from apps/core/backend context.
# All database code is now included in backend/src/database.
#
# Build context: apps/core/backend
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

# Copy backend package
COPY pyproject.toml /app/backend/
WORKDIR /app/backend

# Install dependencies with uv
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy backend source code
COPY src /app/backend/src

# Set Python path to include backend src
ENV PYTHONPATH=/app/backend/src

# Set working directory to src for uvicorn
WORKDIR /app/backend/src

# Expose port
EXPOSE 8000

# Default command
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
