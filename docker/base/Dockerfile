FROM python:3.10

RUN \
  useradd -m engine && \
  apt-get update && \
  apt-get install -y \
    curl \
    python3 \
    python3-pip \
    libssl-dev \
    libmariadb-dev \
    iputils-ping && \
  rm -rf /var/lib/apt/lists/* && \
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
RUN python setup.py egg_info
RUN pip install -r *.egg-info/requires.txt
