FROM ubuntu:latest

RUN apt-get update --fix-missing
RUN apt-get install -y python3.5 wget python3.5-dev build-essential
RUN wget -O /root/get-pip.py https://bootstrap.pypa.io/get-pip.py
RUN python3.5 /root/get-pip.py
RUN rm /root/get-pip.py

COPY . /app
WORKDIR /app

RUN cp engine.conf.inc engine.conf
RUN sed -i -e 's/DEBUG = True/DEBUG = False/g' scoring_engine/web/settings.cfg

RUN pip install -e .

RUN python3.5 ./bin/populate_db

CMD python3.5 run.py
