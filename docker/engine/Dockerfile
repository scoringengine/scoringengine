ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest
FROM ${BASE_IMAGE}

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine

CMD ["/app/bin/engine"]
