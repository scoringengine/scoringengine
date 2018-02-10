FROM python:latest

RUN \
  apt-get update && \
  apt-get install -y curl && \
  apt-get install -y mysql-client

COPY setup.py /app/setup.py
COPY scoring_engine /app/scoring_engine
COPY bin /app/bin
COPY docker/engine.conf.inc /app/engine.conf
COPY docker/wait-for-bootstrap.sh /app

WORKDIR /app
RUN pip install -e .

# SSH Check
RUN pip install paramiko

# Elasticsearch Check
RUN pip install requests

# SMB Check
RUN pip install pysmb

CMD ["./wait-for-bootstrap.sh", "bootstrap", "sh", "/app/bin/worker"]
