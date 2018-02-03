FROM python:latest

COPY setup.py /app/setup.py
COPY scoring_engine /app/scoring_engine
COPY bin /app/bin
COPY run.py /app/run.py
COPY docker/engine.conf.inc /app/engine.conf
COPY docker/wait-for-bootstrap.sh /app

WORKDIR /app

RUN pip install -e .

EXPOSE 5000


#CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "run.py"]
#CMD ["./wait-for-bootstrap.sh", "bootstrap", "uwsgi", "--enable-threads", "-b", "32768", "--processes", "2", "--threads", "2", "--socket", "0.0.0.0:5000", "--wsgi-file", "/app/run.py"]
CMD ["./wait-for-bootstrap.sh", "bootstrap", "uwsgi", "--enable-threads", "-b", "32768", "--processes", "2", "--socket", "0.0.0.0:5000", "--wsgi-file", "/app/run.py", "--stats", "/tmp/stats.socket"]
