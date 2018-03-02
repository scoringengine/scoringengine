FROM base:latest

RUN \
  apt-get update && \
  apt-get install -y curl && \
  apt-get install -y mysql-client

# SSH Check
RUN pip install paramiko

# Elasticsearch Check
RUN pip install requests

# SMB Check
RUN pip install pysmb

# DNS Check
RUN apt-get install -y dnsutils

COPY bin/worker /app/bin/worker

CMD ["./wait-for-it.sh", "redis:6379", "--", "sh", "/app/bin/worker"]
