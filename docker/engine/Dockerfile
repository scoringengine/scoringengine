ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest
FROM ${BASE_IMAGE}

USER root

RUN mkdir -p /var/check_outputs && chown -R engine:engine /var/check_outputs

USER engine

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine

CMD ["/app/bin/engine"]
