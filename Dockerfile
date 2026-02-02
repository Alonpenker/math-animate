FROM python:3.11-slim

# Install system dependencies for postgreSQL and Docker CLI
RUN apt-get update && apt-get install -y libpq-dev gcc curl docker.io

# Clean up apt cache
RUN rm -rf /var/lib/apt/lists/*

# Install uv (package manager)
RUN pip install uv

WORKDIR /app
COPY . .

# Create virtual environment and install dependencies
RUN uv sync --frozen
