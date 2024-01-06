FROM scoringengine/base

USER root

RUN apt-get update

RUN apt-get install -y \
    # ICMP Check
    iputils-ping \
    # HTTP/S Check
    curl \
    # MySQL Check
    default-mysql-client \
    # LDAP Check
    ldap-utils \
    # VNC Check
    medusa \
    # DNS Check
    dnsutils \
    # Postgresql Check
    postgresql-client \
    # OpenVPN Check
    openvpn iproute2 sudo \
    # RDP Check
    freerdp2-x11 xvfb \
    # NFS Check
    libnfs-dev

RUN pip install -I \
    # NFS Check
    "libnfs==1.0.post4" \
    # WinRM Check
    "pywinrm>=0.4.1,<0.4.2" \
    # Elasticsearch Check
    "requests>=2.21,<2.22" \
    # SMB Check
    "pysmb>=1.1,<1.2" \
    # Telnet Check
    "telnetlib3==1.0.1" \
    # SSH Check
    "paramiko==2.11.0"

# MSSQL Check
RUN \
  curl -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb && \
  dpkg -i /tmp/packages-microsoft-prod.deb && \
  apt-get update && \
  ACCEPT_EULA=Y apt-get install -y \
    mssql-tools18 \
    sqlcmd \
    unixodbc-dev

RUN rm -rf /var/lib/apt/lists/*

COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers

USER engine

COPY scoring_engine /app/scoring_engine
RUN pip install -e .

#CMD ["sh", "-c", "Xvfb :1 -screen 0 1024x768x16 & /app/bin/worker"]
CMD sh -c 'Xvfb :1 -screen 0 1024x768x16 & /app/bin/worker'
