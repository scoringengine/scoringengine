ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest
FROM ${BASE_IMAGE}

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
# Note: update docker/worker/Dockerfile as well when changing playwright version
RUN pip install --no-cache-dir -I "pytest-playwright>=0.7.0,<0.8"

CMD ["/app/bin/engine"]
