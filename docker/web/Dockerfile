FROM scoringengine/base

USER engine

COPY bin/web /app/bin/web

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

CMD ["./wait-for-container.sh", "bootstrap", "uwsgi", "--socket", ":5000", "--wsgi-file", "bin/web", "--master", "--processes", "4", "--threads", "2", "--stats", "0.0.0.0:9191", "--stats-http"]

EXPOSE 5000
