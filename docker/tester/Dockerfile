FROM base:latest

COPY tests /app/tests

USER root

RUN pip install -r /app/tests/requirements.txt

COPY .flake8 /app/.flake8
