FROM base:latest

COPY bin/engine /app/bin/engine

CMD ["./wait-for-container.sh", "bootstrap", "python", "/app/bin/engine"]
