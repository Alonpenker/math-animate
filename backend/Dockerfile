FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

FROM python:3.13-slim

RUN apt-get update && apt-get install -y libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

RUN pip install uv

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . .
