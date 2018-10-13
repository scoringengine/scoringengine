FROM base:latest

COPY bin/populate_db /app/bin/populate_db

CMD ["./wait-for-port.sh", "mysql:3306", "--", "python", "/app/bin/populate_db"]
