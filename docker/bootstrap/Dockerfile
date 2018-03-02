FROM base:latest

COPY bin/populate_db /app/bin/populate_db

CMD ["./wait-for-it.sh", "mysql:3306", "--", "python", "/app/bin/populate_db"]
