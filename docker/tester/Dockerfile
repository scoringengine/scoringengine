FROM base:latest

COPY tests /app/tests

USER root

RUN pip install -r /app/tests/requirements.txt
RUN curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > /app/cc-test-reporter
RUN chmod +x /app/cc-test-reporter
