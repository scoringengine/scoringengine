FROM base:latest

USER root

RUN \
  apt-get update && \
  apt-get install -y apt-transport-https && \
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

# Postgresql Check
RUN apt-get install -y postgresql-client

# MSSQL Check
RUN curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
# Package Repo for Ubuntu 16.04
#RUN curl -s https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
# Package Repo for Debian 9 (Docker Hub Python Image)
RUN echo "deb [arch=amd64] https://packages.microsoft.com/debian/9/prod "stretch" main" >> /etc/apt/sources.list.d/msprod.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y locales mssql-tools unixodbc-dev
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen

# RDP Check
RUN apt-get install -y freerdp-x11

COPY bin/worker /app/bin/worker

USER engine

CMD ["./wait-for-port.sh", "redis:6379", "/app/bin/worker"]
