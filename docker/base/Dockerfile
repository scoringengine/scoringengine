FROM python:3.13-slim

RUN \
  useradd -m engine && \
  apt-get update && \
  apt-get install -y \
    build-essential \
    curl \
    gcc \
    libssl-dev \
    libmariadb-dev \
    iputils-ping && \
    # python3.13-dev && \
  rm -rf /var/lib/apt/lists/* && \
  python3 -m ensurepip --upgrade && \
  mkdir /app

COPY docker/wait-for-container.sh /app/wait-for-container.sh
COPY docker/wait-for-port.sh /app/wait-for-port.sh
COPY setup.py /app/setup.py
COPY docker/engine.conf.inc /app/engine.conf

WORKDIR /app

USER root

RUN chown -R engine:engine /app

USER engine

# Needed for celery/uwsgi
ENV PATH=/home/engine/.local/bin:$PATH

# Copy over files required for setup.py
COPY scoring_engine/__init__.py /app/scoring_engine/__init__.py
COPY scoring_engine/version.py /app/scoring_engine/version.py
COPY scoring_engine/config.py /app/scoring_engine/config.py
COPY scoring_engine/config_loader.py /app/scoring_engine/config_loader.py

# Only install dependencies, don't install scoring engine
# Credit goes to https://stackoverflow.com/a/53251585
# RUN pip install --upgrade pip setuptools wheel && \
#     python setup.py egg_info && \
#     pip install -r *.egg-info/requires.txt

RUN pip install --no-cache-dir --upgrade pip setuptools wheel cython && \
    python setup.py egg_info && \
    pip install -r *.egg-info/requires.txt