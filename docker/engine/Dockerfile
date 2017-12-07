FROM python:latest

ADD . /app
WORKDIR /app
RUN pip install -e .

CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "/app/bin/engine"]
