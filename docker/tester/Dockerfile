FROM base:latest

COPY tests /app/tests

USER root

RUN \
  apt-get update && \
  apt-get install -y curl && \
  curl -s -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 -o /usr/bin/cc-test-reporter && \
  chmod +x /usr/bin/cc-test-reporter

COPY bin /app/bin
COPY .flake8 /app/.flake8

USER engine

RUN pip install -r /app/tests/requirements.txt
