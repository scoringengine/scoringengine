ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest
FROM ${BASE_IMAGE}

COPY bin/setup /app/bin/setup
COPY bin/competition.yaml /app/bin/competition.yaml

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

CMD ["python", "/app/bin/setup"]
