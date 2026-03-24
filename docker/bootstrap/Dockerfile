ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest
FROM ${BASE_IMAGE}

COPY bin/setup /app/bin/setup
COPY bin/migrate /app/bin/migrate
COPY bin/competition.yaml /app/bin/competition.yaml

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

COPY scoring_engine /app/scoring_engine

CMD ["python", "/app/bin/setup"]
