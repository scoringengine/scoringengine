# syntax=docker/dockerfile:1
FROM scoringengine/base

USER root

RUN \
  curl -s -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 -o /usr/bin/cc-test-reporter && \
  chmod +x /usr/bin/cc-test-reporter

COPY bin /app/bin

# Set permissions for volume to be mounted
RUN \
  mkdir /app/artifacts && \
  chown engine:engine /app/artifacts

USER engine

# Install test deps BEFORE copying tests for better layer caching
COPY tests/requirements.txt /tmp/test-requirements.txt
RUN --mount=type=cache,target=/home/engine/.cache/pip \
    pip install -r /tmp/test-requirements.txt

COPY scoring_engine /app/scoring_engine
RUN --mount=type=cache,target=/home/engine/.cache/pip \
    pip install -e .
COPY tests /app/tests
