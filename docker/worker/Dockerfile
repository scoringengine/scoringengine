FROM scoringengine/base

USER root

RUN \
  apt-get update && \
  # apt-get install -y apt-transport-https software-properties-common
  apt-get install -y apt-transport-https gpg

# ICMP Check
RUN apt-get install -y iputils-ping

# HTTP/S Check
RUN apt-get install -y curl

# MySQL Check
RUN apt-get install -y default-mysql-client

# LDAP Check
RUN apt-get install -y ldap-utils

# VNC Check
RUN apt-get install -y medusa

# SSH Check
# RUN pip install -I "cryptography>=3.4,<3.5"
RUN pip install "paramiko==3.5.0"

# WinRM Check
RUN pip install -I "pywinrm>=0.5.0,<0.6"

# Elasticsearch Check
RUN pip install -I "requests>=2.32.3,<2.33"

# SMB Check
RUN pip install -I "pysmb>=1.2,<1.3"

# DNS Check
RUN apt-get install -y dnsutils

# Postgresql Check
RUN apt-get install -y postgresql-client

# MSSQL Check
# RUN \
  # curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
  # Package Repo for Ubuntu 16.04
  # curl -s https://packages.microsoftdcom/config/ubuntu/18.04/prod.list | tee /etc/apt/sources.list.d/msprod.list && \
  # apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EB3E94ADBE1229CF
  # Package Repo for Debian 9 (Docker Hub Python Image)
  # echo "deb [arch=amd64] https://packages.microsoft.com/debian/9/prod "stretch" main" >> /etc/apt/sources.list.d/msprod.list && \
  # Package Repo for Debian 11 (Docker Hub Python Image)
  # echo "deb [arch=amd64] https://packages.microsoft.com/debian/11/prod \"bullseye\" main" >> /etc/apt/sources.list.d/msprod.list && \
  # apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EB3E94ADBE1229CF
  # curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
  # apt-add-repository https://packages.microsoft.com/debian/11/prod && \
  # apt-get update && \
  # ACCEPT_EULA=Y apt-get install -y \
    # locales \
    # mssql-tools \
    # unixodbc-dev && \
  # echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
  # locale-gen
RUN \
  curl -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb && \
  dpkg -i /tmp/packages-microsoft-prod.deb && \
  # curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
  # curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/msprod.list && \
  apt-get update && \
  ACCEPT_EULA=Y apt-get install -y \
    mssql-tools18 \
    sqlcmd \
    unixodbc-dev

# RDP Check
# freerdp2-x11 was renamed to freerdp3-x11 on newer distributions
# Some distributions ship only a generic "freerdp" package
RUN apt-get update && \
    (apt-get install -y freerdp2-x11 || apt-get install -y freerdp3-x11 || apt-get install -y freerdp)
RUN apt-get install -y xvfb

# NFS Check
RUN apt-get install -y libnfs-dev
# Pin to the last published Python binding for libnfs
RUN pip install -I "libnfs==1.0.post4"

# Telnet Check
RUN pip install -I "telnetlib3==1.0.1"

# Playwright-based advanced web checks
# Note: update docker/engine/Dockerfile as well when changing playwright version
RUN pip install -I "pytest-playwright>=0.7.0,<0.8"
RUN playwright install-deps

# OpenVPN Check
RUN apt-get install -y openvpn iproute2 sudo

RUN rm -rf /var/lib/apt/lists/*

COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers

USER engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .
RUN playwright install chromium

# Xvfb is a virtual X server which tricks freerdp2
# into thinking it has a screen. This is used for
# RDP scorechecks.
CMD Xvfb :1 -screen 0 1024x768x16 & /app/bin/worker
