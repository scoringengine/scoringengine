FROM scoringengine/base

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
# Note: update docker/worker/Dockerfile as well when changing playwright version
RUN pip install -I "pytest-playwright>=0.7.0,<0.8"

CMD ["/app/bin/engine"]
