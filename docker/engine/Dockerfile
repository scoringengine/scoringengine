FROM scoringengine/base

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

CMD ["./wait-for-container.sh", "bootstrap", "/app/bin/engine"]
