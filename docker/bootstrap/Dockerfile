FROM scoringengine/base

COPY bin/setup /app/bin/setup
COPY bin/competition.yaml /app/bin/competition.yaml

CMD ["./wait-for-port.sh", "mysql:3306", "python", "/app/bin/setup"]
