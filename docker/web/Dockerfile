FROM scoringengine/base

COPY bin/web /app/bin/web

CMD ["./wait-for-container.sh", "bootstrap", "/app/bin/web"]

EXPOSE 5000
