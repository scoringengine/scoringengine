Worker
------

Docker Worker Images
^^^^^^^^^^^^^^^^^^^^

Three Docker worker images are available, allowing you to choose the right balance
of image size vs. check coverage for your competition:

**Full Worker (Monolith)** - ``docker/worker/Dockerfile``
  Contains all 28 service check dependencies. Use this if you want a single worker
  that can handle any check type. Largest image size (~1.5GB).

  .. code-block:: bash

     docker-compose up worker

**Standard Worker** - ``docker/worker/Dockerfile.standard``
  Lightweight worker for common checks. Excludes MSSQL, Playwright, RDP, VNC,
  OpenVPN, and NFS dependencies. Approximately 400MB smaller than the full image.

  Supported checks:
    - ICMP, DNS, HTTP, HTTPS
    - SSH, Telnet, WinRM
    - MySQL, PostgreSQL
    - FTP, SMB, LDAP
    - SMTP, SMTPS
    - Elasticsearch, Wordpress

  .. code-block:: bash

     docker-compose --profile split-workers up worker-standard

**Heavy Worker** - ``docker/worker/Dockerfile.heavy``
  Worker for specialized checks requiring heavy dependencies.

  Supported checks:
    - MSSQL (Microsoft SQL Server tools)
    - RDP (freerdp + Xvfb)
    - VNC, POP3, IMAP (medusa)
    - OpenVPN (openvpn client)
    - NFS (nfs-common)
    - Playwright-based webapp checks (Chromium)

  .. code-block:: bash

     docker-compose --profile split-workers up worker-heavy

Worker Queue Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

Workers listen to specific Celery queues. Services are routed to workers based on
their ``worker_queue`` setting.

**Environment Variable:**
  Set ``SCORINGENGINE_WORKER_QUEUE`` to specify which queue a worker monitors:

  .. code-block:: bash

     SCORINGENGINE_WORKER_QUEUE=heavy docker-compose up worker-heavy

**Competition YAML:**
  Services specify their target queue using the ``worker_queue`` field:

  .. code-block:: yaml

     services:
       - name: MSSQL
         check_name: MSSQLCheck
         host: 192.168.1.10
         port: 1433
         worker_queue: heavy  # Route to heavy worker
         points: 100
         # ...

       - name: HTTP
         check_name: HTTPCheck
         host: 192.168.1.20
         port: 80
         # worker_queue defaults to "main" if not specified
         points: 100
         # ...

**Default Queues:**
  - ``main`` - Default queue for standard checks (ICMP, DNS, HTTP, SSH, MySQL, etc.)
  - ``heavy`` - Queue for heavy checks (MSSQL, RDP, VNC, OpenVPN, NFS, Playwright)

Split Worker Deployment Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To deploy with split workers instead of the monolith:

.. code-block:: bash

   # Build and start split workers
   docker-compose --profile split-workers up -d worker-standard worker-heavy

   # Or build all images including split workers
   docker-compose --profile split-workers build

Then configure your ``competition.yaml`` to route heavy checks:

.. code-block:: yaml

   services:
     # These use the default "main" queue -> worker-standard
     - name: HTTP
       check_name: HTTPCheck
       # ...

     - name: SSH
       check_name: SSHCheck
       # ...

     # These use "heavy" queue -> worker-heavy
     - name: MSSQL
       check_name: MSSQLCheck
       worker_queue: heavy
       # ...

     - name: RDP
       check_name: RDPCheck
       worker_queue: heavy
       # ...

Check-to-Queue Mapping Reference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following table shows recommended queue assignments:

+-------------------------+------------------+----------------------------------+
| Check                   | Recommended      | Notes                            |
|                         | Queue            |                                  |
+=========================+==================+==================================+
| ICMPCheck               | main             | ping (iputils-ping)              |
+-------------------------+------------------+----------------------------------+
| DNSCheck                | main             | dig (dnsutils)                   |
+-------------------------+------------------+----------------------------------+
| HTTPCheck, HTTPSCheck   | main             | curl                             |
+-------------------------+------------------+----------------------------------+
| SSHCheck                | main             | paramiko                         |
+-------------------------+------------------+----------------------------------+
| TelnetCheck             | main             | telnetlib3                       |
+-------------------------+------------------+----------------------------------+
| WinRMCheck              | main             | pywinrm                          |
+-------------------------+------------------+----------------------------------+
| MYSQLCheck              | main             | mysql-client                     |
+-------------------------+------------------+----------------------------------+
| POSTGRESQLCheck         | main             | postgresql-client                |
+-------------------------+------------------+----------------------------------+
| FTPCheck                | main             | Python ftplib                    |
+-------------------------+------------------+----------------------------------+
| SMBCheck                | main             | pysmb                            |
+-------------------------+------------------+----------------------------------+
| LDAPCheck               | main             | ldap-utils                       |
+-------------------------+------------------+----------------------------------+
| SMTPCheck, SMTPSCheck   | main             | Python smtplib                   |
+-------------------------+------------------+----------------------------------+
| ElasticsearchCheck      | main             | requests                         |
+-------------------------+------------------+----------------------------------+
| WordpressCheck          | main             | curl                             |
+-------------------------+------------------+----------------------------------+
| MSSQLCheck              | **heavy**        | mssql-tools (~200MB)             |
+-------------------------+------------------+----------------------------------+
| RDPCheck                | **heavy**        | freerdp + Xvfb                   |
+-------------------------+------------------+----------------------------------+
| VNCCheck                | **heavy**        | medusa                           |
+-------------------------+------------------+----------------------------------+
| POP3Check, POP3SCheck   | **heavy**        | medusa                           |
+-------------------------+------------------+----------------------------------+
| IMAPCheck, IMAPSCheck   | **heavy**        | medusa                           |
+-------------------------+------------------+----------------------------------+
| OpenVPNCheck            | **heavy**        | openvpn + sudo                   |
+-------------------------+------------------+----------------------------------+
| NFSCheck                | **heavy**        | nfs-common + mount               |
+-------------------------+------------------+----------------------------------+
| WebappNginxdefaultpage, | **heavy**        | Playwright + Chromium (~500MB)   |
| WebappScoringengine     |                  |                                  |
+-------------------------+------------------+----------------------------------+

Manual Installation
^^^^^^^^^^^^^^^^^^^

For manual (non-Docker) installations, follow the steps below.

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

  # Package name changed in newer distributions
  apt-get install -y freerdp2-x11 || apt-get install -y freerdp3-x11 || apt-get install -y freerdp

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

  apt-get install -y nfs-common

Install dependencies for OpenVPN check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y openvpn iproute2 sudo
  cp /home/engine/scoring_engine/src/docker/worker/sudoers /etc/sudoers

Install dependencies for Telnet check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate && pip install -I "telnetlib3==1.0.1"

