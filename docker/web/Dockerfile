FROM scoringengine/base

USER root

# Inject upload folder
RUN mkdir -p /var/uploads && chown -R engine:engine /var/uploads

# Install curl for docker health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

USER engine

COPY bin/web /app/bin/web

CMD ["uwsgi", "--socket", ":5000", "--wsgi-file", "bin/web", "--master", "--processes", "4", "--threads", "2", "--stats", "0.0.0.0:9191", "--stats-http", "--buffer-size", "32768", "--post-buffering", "8192"]

EXPOSE 5000
