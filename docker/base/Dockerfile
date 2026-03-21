# syntax=docker/dockerfile:1
# Stage 1: Builder — compile C extensions into a venv
ARG PYTHON_VERSION=3.14.3-slim-bookworm
FROM python:${PYTHON_VERSION} AS builder

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      libmariadb-dev \
      libmariadb-dev-compat \
      libssl-dev \
      pkg-config

RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Install deps first (cached until pyproject.toml changes)
COPY pyproject.toml /tmp/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install $(python3 -c "\
import tomllib, pathlib; \
d = tomllib.loads(pathlib.Path('/tmp/pyproject.toml').read_text()); \
print(' '.join(d['project']['dependencies']))")

# Stage 2: Runtime — slim image with only runtime libs
ARG PYTHON_VERSION=3.14.3-slim-bookworm
FROM python:${PYTHON_VERSION}

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    set -eux; \
    useradd -m -u 1000 engine; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      curl \
      iputils-ping \
      libmariadb3 \
      libssl3 \
    && mkdir /app \
    && chown engine:engine /app

COPY --from=builder --chown=engine:engine /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY --chown=engine:engine pyproject.toml /app/pyproject.toml
COPY --chown=engine:engine docker/engine.conf.inc /app/engine.conf

WORKDIR /app

USER engine

COPY --chown=engine:engine scoring_engine /app/scoring_engine

# Fast — deps already in venv, just creates egg-link
RUN --mount=type=cache,target=/home/engine/.cache/pip \
    pip install -e .
