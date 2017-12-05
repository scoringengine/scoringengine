FROM python:latest

ADD . /app

WORKDIR /app

RUN pip install -e .

EXPOSE 5000

CMD ["./wait-for-it.sh", "mysql:3306", "--", "python", "run.py"]
