FROM ubuntu:bionic

RUN \
  useradd -m engine && \
  apt-get update && \
  apt-get install -y \
    python3 \
    python3-pip \
    libmysqlclient-dev \
    iputils-ping && \
  rm -rf /var/lib/apt/lists/* && \
  pip3 install virtualenv && \
  mkdir /app && \
  virtualenv -p `which python3` /venv

COPY docker/wait-for-container.sh /app/wait-for-container.sh
COPY docker/wait-for-port.sh /app/wait-for-port.sh
COPY setup.py /app/setup.py
COPY docker/engine.conf.inc /app/engine.conf
COPY scoring_engine /app/scoring_engine

WORKDIR /app

USER root

RUN \
  chown -R engine:engine /app && \
  chown -R engine:engine /venv

USER engine

# Automatically source into python virtual environment
ENV PATH=/venv/bin:$PATH

RUN pip install -e .
