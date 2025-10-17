FROM scoringengine/base

ARG WITH_PLAYWRIGHT=false

USER root

RUN \
  curl -s -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 -o /usr/bin/cc-test-reporter && \
  chmod +x /usr/bin/cc-test-reporter

RUN if [ "$WITH_PLAYWRIGHT" = "true" ]; then \
      pip install -I "pytest-playwright>=0.7.0,<0.8" && \
      playwright install-deps; \
    fi

COPY bin /app/bin
COPY .flake8 /app/.flake8

# Set permissions for volume to be mounted
RUN \
  mkdir /app/artifacts && \
  chown engine:engine /app/artifacts

USER engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
COPY tests /app/tests
RUN pip install -r /app/tests/requirements.txt
RUN if [ "$WITH_PLAYWRIGHT" = "true" ]; then \
      pip install -r /app/tests/requirements-webui.txt && \
      playwright install chromium; \
    fi

