Worker
------

Modify hostname
^^^^^^^^^^^^^^^
::

  hostname <INSERT CUSTOM HOSTNAME HERE>

Setup worker service (run as root)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/configs/worker.service /etc/systemd/system/scoring_engine-worker.service

Modify configuration
^^^^^^^^^^^^^^^^^^^^
Change REDIS host/port/password fields to main engine host::
::

  vi /home/engine/scoring_engine/src/engine.conf

Modify worker to customize number of processes. Append '--concurrency <num of processes>' to the celery command line. If not specified, it defaults to # of CPUs.
::

  vi /home/engine/scoring_engine/src/bin/worker

Start worker service (must run as root)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  systemctl enable scoring_engine-worker
  systemctl start scoring_engine-worker

Monitor worker
^^^^^^^^^^^^^^
::

  journalctl -f _SYSTEMD_UNIT=scoring_engine-worker.service
  tail -f /var/log/scoring_engine/worker.log

Install dependencies for DNS check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y dnsutils

Install dependencies for HTTP/HTTPS check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y curl

Install dependencies for most of the checks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y medusa

Install dependencies for SSH check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate && pip install -I "cryptography>=2.4,<2.5" && pip install "paramiko>=2.4,<2.5"

Install dependencies for LDAP check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y ldap-utils

Install dependencies for Postgresql check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y postgresql-client

Install dependencies for Elasticsearch check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate && pip install -I "requests>=2.21,<2.22"

Install dependencies for SMB check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate && pip install -I "pysmb>=1.1,<1.2"

Install dependencies for RDP check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y freerdp-x11

Install dependencies for MSSQL check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y apt-transport-https
  curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
  curl -s https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
  apt-get update
  ACCEPT_EULA=Y apt-get install -y locales mssql-tools unixodbc-dev
  echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
  locale-gen

Install dependencies for SMTP/SMTPS check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/scoring_engine/checks/bin/smtp_check /usr/bin/smtp_check
  cp /home/engine/scoring_engine/src/scoring_engine/checks/bin/smtps_check /usr/bin/smtps_check
  chmod a+x /usr/bin/smtp_check
  chmod a+x /usr/bin/smtps_check

Install dependencies for NFS check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y libnfs-dev
  source /home/engine/scoring_engine/env/bin/activate && pip install -I "libnfs==1.0.post4"

Install dependencies for OpenVPN check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y openvpn iproute2 sudo
  cp /home/engine/scoring_engine/src/docker/worker/sudoers /etc/sudoers

Install dependencies for Telnet check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate && pip install -I "telnetlib3==1.0.1"

