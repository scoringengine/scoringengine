FROM python:latest

ADD . /app
WORKDIR /app
RUN pip install -e .

CMD ["./wait-for-it.sh", "mysql:3306", "--", "sh", "/app/bin/worker"]
