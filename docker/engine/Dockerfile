FROM base:latest

COPY bin/engine /app/bin/engine

CMD ["./wait-for-container.sh", "bootstrap", "/app/bin/engine"]
