FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/backend \
    PATH="/app/backend/.venv/bin:$PATH"

COPY backend/pyproject.toml backend/uv.lock /app/backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev --no-install-project

COPY backend /app/backend
COPY shared /app/shared
COPY bot /app/bot
RUN uv sync --frozen --no-dev