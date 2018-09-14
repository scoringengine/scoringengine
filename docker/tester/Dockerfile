FROM base:latest

COPY tests /app/tests

USER root

RUN pip install -r /app/tests/requirements.txt

RUN curl -s -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > /usr/bin/cc-test-reporter
RUN chmod +x /usr/bin/cc-test-reporter

COPY .flake8 /app/.flake8
