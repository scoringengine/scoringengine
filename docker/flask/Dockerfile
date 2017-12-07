FROM python:latest

ADD . /app

WORKDIR /app

RUN pip install -e .

EXPOSE 5000

CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "run.py"]
