FROM scoringengine/base

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

CMD ["/app/bin/engine"]
