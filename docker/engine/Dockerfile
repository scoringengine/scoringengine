FROM base:latest

COPY bin/engine /app/bin/engine

CMD ["./wait-for-container.sh", "bootstrap", "/usr/local/bin/python", "/app/bin/engine"]
