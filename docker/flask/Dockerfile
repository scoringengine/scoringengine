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


CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "run.py"]
