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

# MSSQL Check
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
# Package Repo for Ubuntu 16.04
#RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
# Package Repo for Debian 8 (Docker Hub Python Image)
RUN echo "deb [arch=amd64] https://packages.microsoft.com/debian/8/prod jessie main" >> /etc/apt/sources.list.d/msprod.list
RUN apt-get update 
RUN ACCEPT_EULA=Y apt-get install -y locales mssql-tools unixodbc-dev
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen

COPY bin/worker /app/bin/worker

USER engine

CMD ["./wait-for-it.sh", "redis:6379", "--", "sh", "/app/bin/worker"]
