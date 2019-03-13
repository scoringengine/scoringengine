FROM scoringengine/base

USER root

RUN \
  apt-get update && \
  apt-get install -y apt-transport-https

# ICMP Check
RUN apt-get install -y iputils-ping

# HTTP/S Check
RUN apt-get install -y curl

# MySQL Check
RUN apt-get install -y mysql-client

# LDAP Check
RUN apt-get install -y ldap-utils

# VNC Check
RUN apt-get install -y medusa

# SSH Check
RUN pip install -I "cryptography>=2.4,<2.5"
RUN pip install "paramiko>=2.4,<2.5"

# Elasticsearch Check
RUN pip install -I "requests>=2.21,<2.22"

# SMB Check
RUN pip install -I "pysmb>=1.1,<1.2"

# DNS Check
RUN apt-get install -y dnsutils

# Postgresql Check
RUN apt-get install -y postgresql-client

# MSSQL Check
RUN \
  curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
  # Package Repo for Ubuntu 16.04
  curl -s https://packages.microsoft.com/config/ubuntu/18.04/prod.list | tee /etc/apt/sources.list.d/msprod.list && \
  # Package Repo for Debian 9 (Docker Hub Python Image)
  # echo "deb [arch=amd64] https://packages.microsoft.com/debian/9/prod "stretch" main" >> /etc/apt/sources.list.d/msprod.list && \
  apt-get update && \
  ACCEPT_EULA=Y apt-get install -y \
    locales \
    mssql-tools \
    unixodbc-dev && \
  echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
  locale-gen

# RDP Check
RUN apt-get install -y freerdp-x11

# NFS Check
RUN apt-get install -y libnfs-dev
RUN pip install -I "libnfs==1.0.post4"

# OpenVPN Check
RUN apt-get install -y openvpn iproute2 sudo

RUN rm -rf /var/lib/apt/lists/*

COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers

USER engine

CMD ["./wait-for-port.sh", "redis:6379", "/app/bin/worker"]
