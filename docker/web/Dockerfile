FROM scoringengine/base

USER root

# Install curl for docker health check
RUN \
  apt-get update && \
  apt-get install -y curl && \
  rm -rf /var/lib/apt/lists/*

USER engine

COPY bin/web /app/bin/web

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

CMD ["./wait-for-container.sh", "bootstrap", "/app/bin/web"]

EXPOSE 5000
