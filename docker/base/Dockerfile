FROM ubuntu:latest

RUN \
  apt-get update --fix-missing && \
  apt-get install -y --fix-missing \
    python3.5 \
    python3.5-dev \
    build-essential \
    curl && \
  curl -o /root/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
  python3.5 /root/get-pip.py && \
  rm /root/get-pip.py && \
  mkdir /app && \
  mkdir /app/data && \
  ln -s /usr/bin/python3.5 /usr/bin/python

COPY setup.py /app/setup.py
COPY scoring_engine /app/scoring_engine
COPY bin /app/bin

WORKDIR /app

RUN pip install -e .

COPY docker/base/files/engine.conf.inc /app/engine.conf
