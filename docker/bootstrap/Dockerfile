FROM base:latest

WORKDIR /app

CMD ["./wait-for-it.sh", "mysql:3306", "--", "python", "/app/bin/populate_db"]
