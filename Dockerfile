FROM python:3.13-slim

# Install system dependencies for postgreSQL and Docker CLI and clean apt cache
RUN apt-get update && apt-get install -y libpq-dev gcc curl docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install uv (package manager)
RUN pip install uv

WORKDIR /app

# Copy only dependency manifests
COPY pyproject.toml uv.lock ./

# Install deps (cached unless lockfile changes)
RUN uv sync --frozen

# Copy application code
COPY . .
