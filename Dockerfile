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
  sed -i -e 's/DEBUG = True/DEBUG = False/g' scoring_engine/web/settings.cfg && \
  sed -i -e 's/about_us_page_content =.*/about_us_page_content = <h4>Use the following credentials to login<\/h4><ul><li>whiteteamuser:testpass<\/li><li>team1user1:testpass<\/li><li>team2user1:testpass<\/li><li>redteamuser:testpass<\/li><\/ul>/g' engine.conf && \
  pip install -e .

RUN python3.5 ./bin/populate_db > /dev/null

EXPOSE 5000
CMD python3.5 run.py
