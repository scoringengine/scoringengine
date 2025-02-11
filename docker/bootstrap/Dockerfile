FROM scoringengine/base

COPY bin/setup /app/bin/setup
COPY bin/competition.yaml /app/bin/competition.yaml

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
RUN pip install -I "pytest-playwright==0.6.2"

CMD ["./wait-for-port.sh", "mysql:3306", "python", "/app/bin/setup"]
