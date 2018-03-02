FROM base:latest

COPY run.py /app/run.py

CMD ["./wait-for-bootstrap.sh", "bootstrap", "python", "run.py"]

EXPOSE 5000
