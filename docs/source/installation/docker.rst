Docker
======

.. note:: It takes a minute or 2 for all of the containers to start up and get going!

.. important:: For airgapped/offline competitions with no internet access, see :doc:`airgapped` for complete deployment instructions.

TestBed Environment
-------------------
::

  make rebuild-testbed-new

This command will build, stop any pre-existing scoring engine containers, and start a new environment. As part of the environment, multiple containers will be used as part of the testbed environment.

Environment Variables
---------------------
We use certain environment variables to control the functionality of certain docker containers.

:SCORINGENGINE_OVERWRITE_DB: If set to true, the database will be deleted and then recreated during startup.
:SCORINGENGINE_EXAMPLE: If set to true, the database is populated with sample db, and the engine container will be paused. This is useful for doing development on the web app.

You can set each environment variable before each command executed, for example:
::

  SCORINGENGINE_EXAMPLE=true make rebuild-new


Worker Check Packs
------------------
Check tools are split into packs so you only download what your competition uses. The default worker is the slim **core** image (about 440 MB), which runs most checks: DNS, HTTP(S), ICMP, IMAP/POP3, LDAP, FTP, SMTP, SSH, Telnet, VNC, SMB, WinRM, NFS, OpenVPN, Elasticsearch, Agent and WordPress.

======== ================================== ==============
Pack     Checks                             Adds
======== ================================== ==============
db       MySQL, PostgreSQL, MSSQL           ~170 MB
rdp      RDP                                ~280 MB
browser  Webapp* (Playwright/Chromium)      ~1.1 GB
adcs     ADCSWebEnroll (certipy)            ~100 MB
======== ================================== ==============

Enable packs in ``.env`` (``bin/install --packs db,browser`` writes this for you). Each pack starts its own worker alongside the core worker::

  COMPOSE_PROFILES=db,browser

Or run a single worker with every pack::

  WORKER_TARGET=full

If a service needs a pack that no worker provides, its check fails immediately with ``No worker available for check pack '<pack>'``. The admin **Queues** page then shows the pack's queue (e.g. ``main.browser``) with no workers.

.. note:: **Upgrading:** earlier versions shipped one worker with every tool. If your competition uses RDP, database, Webapp or ADCS checks, set ``COMPOSE_PROFILES`` or ``WORKER_TARGET=full`` before upgrading. For airgapped packages, set them before running ``bin/create-airgapped-package.sh`` so the right worker images are included.

Production Environment
----------------------

Modify the bin/competition.yaml file to configure the engine according to your competition environment. Then, run the following make command to build, and run the scoring engine.

.. warning:: This will delete the previous database, exclude the 'new' part from the command to not rebuild the db.

::

  make rebuild-new

Then, to 'pause' the scoring engine (Ex: At the end of the day)::

  docker-compose -f docker-compose.yml stop engine

To 'unpause' the engine::

  docker-compose -f docker-compose.yml start engine

