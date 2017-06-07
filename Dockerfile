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
RUN sed -i -e 's/about_us_page_content =.*/about_us_page_content = Use the following logins: <ol><li>whiteteamuser:testpass<\/li><li>team1user1:testpass<\/li><li>team2user1:testpass<\/li>redteamuser:testpass<\/li><\/ol>/g' engine.conf

RUN pip install -e .

RUN python3.5 ./bin/populate_db

EXPOSE 5000
CMD python3.5 run.py
