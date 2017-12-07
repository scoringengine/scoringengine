FROM python:latest

ADD . /app
WORKDIR /app
RUN pip install -e .

CMD ["./wait-for-bootstrap.sh", "bootstrap", "sh", "/app/bin/worker"]
