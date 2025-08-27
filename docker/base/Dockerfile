FROM python:3.12-slim-bookworm

RUN set -eux; \
  useradd -m engine; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    libssl-dev \
    pkg-config \
    libmariadb-dev-compat \
    libmariadb-dev \
    iputils-ping \
  ; \
  rm -rf /var/lib/apt/lists/* && \
  python3 -m ensurepip --upgrade && \
  mkdir /app
COPY pyproject.toml /app/pyproject.toml
COPY docker/engine.conf.inc /app/engine.conf

WORKDIR /app

USER root

RUN chown -R engine:engine /app

USER engine

# Needed for celery/uwsgi
ENV PATH=/home/engine/.local/bin:$PATH

COPY scoring_engine /app/scoring_engine

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .
