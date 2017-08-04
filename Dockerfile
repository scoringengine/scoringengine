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
  rm /root/get-pip.py

COPY . /app
WORKDIR /app

RUN \
  cp engine.conf.inc engine.conf && \
  pip install -e .

RUN python3.5 ./bin/populate_db > /dev/null

EXPOSE 5000
CMD python3.5 run.py
