FROM scoringengine/base

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    # allows adding HTTPS apt repos for MSSQL checks
    apt-transport-https \
    # verifies apt repository signatures for MSSQL checks
    gpg \
    # ICMP ping checks
    iputils-ping \
    # HTTP/HTTPS/WordPress checks
    curl \
    # MySQL checks
    default-mysql-client \
    # LDAP checks
    ldap-utils \
    # POP3/IMAP/VNC login checks
    medusa \
    # DNS checks
    dnsutils \
    # PostgreSQL checks
    postgresql-client \
    # NFS checks
    nfs-common \
    # OpenVPN checks
    openvpn \
    # OpenVPN check uses ip command
    iproute2 \
    # OpenVPN check runs openvpn via sudo
    sudo \
  && rm -rf /var/lib/apt/lists/*

RUN curl -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb && \
    dpkg -i /tmp/packages-microsoft-prod.deb && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
      # Microsoft SQL Server checks
      mssql-tools18 \
      # Microsoft SQL Server checks
      sqlcmd \
      # Microsoft SQL Server checks
      unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# freerdp2-x11 was renamed to freerdp3-x11 on newer distributions
# Some distributions ship only a generic "freerdp" package
# RDP checks
RUN apt-get update && (apt-get install -y --no-install-recommends freerdp2-x11 || apt-get install -y --no-install-recommends freerdp3-x11 || apt-get install -y --no-install-recommends freerdp)
RUN apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -I \
    # SSH checks
    "paramiko==3.5.0" \
    # WinRM checks
    "pywinrm>=0.5.0,<0.6" \
    # Elasticsearch checks
    "requests>=2.32.3,<2.33" \
    # SMB checks
    "pysmb>=1.2,<1.3" \
    # Telnet checks
    "telnetlib3==1.0.1"
    
# Playwright-based advanced web checks
# Note: update docker/engine/Dockerfile as well when changing playwright version
RUN pip install -I "pytest-playwright>=0.7.0,<0.8"
RUN playwright install-deps

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
