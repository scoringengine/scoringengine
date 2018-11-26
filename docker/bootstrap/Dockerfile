FROM base:latest

COPY bin/populate_db /app/bin/populate_db
COPY bin/sample_competition.json /app/bin/sample_competition.json

CMD ["./wait-for-port.sh", "mysql:3306", "python", "/app/bin/populate_db"]
