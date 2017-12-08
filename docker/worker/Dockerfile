FROM python:latest

RUN \
  apt-get update && \
  apt-get install -y curl && \
  apt-get install -y sshpass

COPY setup.py /app/setup.py
COPY scoring_engine /app/scoring_engine
COPY bin /app/bin
COPY docker/engine.conf.inc /app/engine.conf
COPY docker/wait-for-bootstrap.sh /app

WORKDIR /app
RUN pip install -e .

CMD ["./wait-for-bootstrap.sh", "bootstrap", "sh", "/app/bin/worker"]
