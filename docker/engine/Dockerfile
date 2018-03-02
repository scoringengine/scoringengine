FROM base:latest

COPY bin/engine /app/bin/engine

CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "/app/bin/engine"]
