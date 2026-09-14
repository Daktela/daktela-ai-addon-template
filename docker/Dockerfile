# Production image. Builds the frontend bundle and the Python environment in
# separate stages, then ships only what is needed to run. See docs/13-deployment.md.

# --- stage 1: the federated frontend bundle --------------------------------
FROM node:26-alpine AS frontend
WORKDIR /build

# Node 26 no longer bundles Corepack, so install it. Corepack is worth the
# extra line: it reads `packageManager` from package.json, so the pnpm version
# is pinned in one place for the image, CI and your machine alike.
RUN npm install -g corepack@latest && corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/.npmrc ./
RUN corepack pnpm install --frozen-lockfile

COPY frontend/ ./
RUN corepack pnpm build

# --- stage 2: the Python environment ---------------------------------------
# `cw-database` depends on psycopg2, which is source-only, so this stage needs
# a compiler and the Postgres client headers. They stay here - the runtime
# image below gets the built virtualenv and nothing else.
FROM python:3.13-slim AS builder
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- stage 3: the addon ----------------------------------------------------
FROM python:3.13-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# libpq5 is the runtime half of libpq-dev: psycopg2 links against it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 addon

COPY --from=builder /app/.venv /app/.venv

COPY server/ ./server/
COPY migrations/ ./migrations/
COPY alembic.ini pyproject.toml ./
COPY --from=frontend /build/dist ./frontend/dist

# ADDON_SETTINGS_FILE usually points into /data. Creating it here means a
# mounted volume inherits this ownership - otherwise the container runs as
# `addon` and cannot write to a root-owned volume.
RUN mkdir -p /data && chown -R addon:addon /app /data
USER addon

EXPOSE 8000

# /liveness and /readiness are the probe targets - see server/health.py.
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
