FROM base:latest

COPY run.py /app/run.py

CMD ["./wait-for-container.sh", "bootstrap", "/usr/local/bin/python", "run.py"]

EXPOSE 5000
