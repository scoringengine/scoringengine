# Stage 1: Builder — compile C extensions into a venv
FROM python:3.14.2-slim-bookworm AS builder

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libssl-dev \
    pkg-config \
    libmariadb-dev-compat \
    libmariadb-dev \
  ; \
  rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Install deps first (cached until pyproject.toml changes)
COPY pyproject.toml /tmp/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir $(python3 -c "\
import tomllib, pathlib; \
d = tomllib.loads(pathlib.Path('/tmp/pyproject.toml').read_text()); \
print(' '.join(d['project']['dependencies']))")

# Stage 2: Runtime — slim image with only runtime libs
FROM python:3.14.2-slim-bookworm

RUN set -eux; \
  useradd -m engine; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    curl \
    libssl3 \
    libmariadb3 \
    iputils-ping \
  ; \
  rm -rf /var/lib/apt/lists/* && \
  mkdir /app && \
  chown engine:engine /app

COPY --from=builder --chown=engine:engine /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY --chown=engine:engine pyproject.toml /app/pyproject.toml
COPY --chown=engine:engine docker/engine.conf.inc /app/engine.conf

WORKDIR /app

USER engine

COPY --chown=engine:engine scoring_engine /app/scoring_engine

# Fast — deps already in venv, just creates egg-link
RUN pip install --no-cache-dir -e .
