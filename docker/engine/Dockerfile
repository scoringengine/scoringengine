FROM scoringengine/base

ARG WITH_PLAYWRIGHT=false

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
# Note: update docker/worker/Dockerfile as well when changing playwright version
RUN if [ "$WITH_PLAYWRIGHT" = "true" ]; then \
    pip install -I "pytest-playwright>=0.7.0,<0.8"; \
  fi

CMD ["/app/bin/engine"]
