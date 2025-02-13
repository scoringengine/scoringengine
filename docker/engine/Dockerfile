FROM scoringengine/base

COPY bin/engine /app/bin/engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
RUN pip install -I "pytest-playwright==0.6.2"

CMD ["./wait-for-container.sh", "bootstrap", "/app/bin/engine"]
