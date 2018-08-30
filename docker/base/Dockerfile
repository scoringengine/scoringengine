FROM python:3.5

RUN \
  mkdir /app && \
  useradd -m engine

COPY docker/wait-for-bootstrap.sh /app
COPY docker/wait-for-it.sh /app
COPY setup.py /app/setup.py
COPY docker/engine.conf.inc /app/engine.conf
COPY scoring_engine /app/scoring_engine

WORKDIR /app

RUN pip install -e .

USER engine
