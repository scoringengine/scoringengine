Airgapped Deployment
====================

.. warning:: For competitions in completely airgapped environments (no internet access), all dependencies must be vendored and pre-loaded before deployment.

Overview
--------

Many cybersecurity competitions run in completely airgapped environments with no internet connectivity. This guide covers how to prepare and deploy Scoring Engine in such environments.

Requirements
------------

Before entering the airgapped environment, you'll need:

- A system with internet access to download and prepare all dependencies
- Docker and Docker Compose installed on both the preparation system and target deployment system
- Sufficient storage for all Docker images (approximately 2-3 GB)
- USB drive or other transfer mechanism to move files to the airgapped environment

Preparation Steps (On Internet-Connected System)
-------------------------------------------------

Automated Package Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to create an airgapped package is using the provided script:

::

  git clone https://github.com/scoringengine/scoringengine.git
  cd scoringengine
  ./bin/create-airgapped-package.sh

This script will:

- Build all Docker images
- Export all images to tar files
- Copy source code
- Create deployment scripts
- Generate a complete package: ``scoringengine-airgapped.tar.gz``

You can then transfer this single file to your airgapped environment.

Manual Package Creation
~~~~~~~~~~~~~~~~~~~~~~~

If you prefer to create the package manually:

1. Clone the Repository
^^^^^^^^^^^^^^^^^^^^^^^^

::

  git clone https://github.com/scoringengine/scoringengine.git
  cd scoringengine

2. Build All Docker Images
^^^^^^^^^^^^^^^^^^^^^^^^^^

Build all required images while you have internet access:

::

  docker-compose build --no-cache

This will download and cache:

- **Base Python image**: ``python:3.14.1-slim-bookworm``
- **Redis**: ``redis:7.0.4``
- **MariaDB**: ``mariadb:10``
- **Nginx**: ``nginx:1.23.1``
- All system packages (apt packages)
- All Python dependencies (pip packages)

3. Export Docker Images
^^^^^^^^^^^^^^^^^^^^^^^

Save all built images to tar files for transfer:

::

  # Create a directory for the image exports
  mkdir -p docker-images

  # Export base images
  docker save python:3.14.1-slim-bookworm -o docker-images/python-base.tar
  docker save redis:7.0.4 -o docker-images/redis.tar
  docker save mariadb:10 -o docker-images/mariadb.tar
  docker save nginx:1.23.1 -o docker-images/nginx.tar

  # Export application images
  docker save scoringengine/base -o docker-images/scoringengine-base.tar
  docker save scoringengine/bootstrap -o docker-images/scoringengine-bootstrap.tar
  docker save scoringengine/engine -o docker-images/scoringengine-engine.tar
  docker save scoringengine/worker -o docker-images/scoringengine-worker.tar
  docker save scoringengine/web -o docker-images/scoringengine-web.tar

4. Create Transfer Package
^^^^^^^^^^^^^^^^^^^^^^^^^^

Package everything needed for airgapped deployment:

::

  # Create deployment package
  mkdir -p scoringengine-airgapped

  # Copy repository
  cp -r . scoringengine-airgapped/scoringengine

  # Move docker images
  mv docker-images scoringengine-airgapped/

  # Create load script
  cat > scoringengine-airgapped/load-images.sh << 'EOF'
  #!/bin/bash
  set -e

  echo "Loading Docker images for airgapped deployment..."

  # Load base images
  docker load -i docker-images/python-base.tar
  docker load -i docker-images/redis.tar
  docker load -i docker-images/mariadb.tar
  docker load -i docker-images/nginx.tar

  # Load application images
  docker load -i docker-images/scoringengine-base.tar
  docker load -i docker-images/scoringengine-bootstrap.tar
  docker load -i docker-images/scoringengine-engine.tar
  docker load -i docker-images/scoringengine-worker.tar
  docker load -i docker-images/scoringengine-web.tar

  echo "All images loaded successfully!"
  docker images | grep -E "(scoringengine|redis|mariadb|nginx|python)"
  EOF

  chmod +x scoringengine-airgapped/load-images.sh

  # Create README
  cat > scoringengine-airgapped/README.txt << 'EOF'
  SCORING ENGINE - AIRGAPPED DEPLOYMENT PACKAGE
  ==============================================

  This package contains everything needed to deploy Scoring Engine
  in an airgapped environment with no internet access.

  PREREQUISITES:
  - Docker installed on target system
  - Docker Compose installed on target system

  DEPLOYMENT STEPS:

  1. Transfer this entire directory to the airgapped system

  2. Load Docker images:
     ./load-images.sh

  3. Navigate to the application directory:
     cd scoringengine

  4. Configure your competition:
     Edit bin/competition.yaml with your competition setup

  5. Start the scoring engine:
     docker-compose up -d

  6. Access the web interface:
     http://localhost (or http://SERVER_IP)

  For detailed documentation, see:
     scoringengine/docs/source/installation/airgapped.rst

  EOF

  # Create compressed archive
  tar czf scoringengine-airgapped.tar.gz scoringengine-airgapped/

  echo "Airgapped deployment package created: scoringengine-airgapped.tar.gz"
  ls -lh scoringengine-airgapped.tar.gz

Alternative: Using Docker Save for All Images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you prefer to save all images in a single command:

::

  docker save \
    python:3.14.1-slim-bookworm \
    redis:7.0.4 \
    mariadb:10 \
    nginx:1.23.1 \
    scoringengine/base \
    scoringengine/bootstrap \
    scoringengine/engine \
    scoringengine/worker \
    scoringengine/web \
    -o all-images.tar

  # Then load on the airgapped system:
  docker load -i all-images.tar

Deployment Steps (In Airgapped Environment)
--------------------------------------------

1. Transfer Package
~~~~~~~~~~~~~~~~~~~

Transfer the ``scoringengine-airgapped.tar.gz`` file to the airgapped system using:

- USB drive
- CD/DVD
- Direct file transfer
- Any approved transfer method

2. Extract Package
~~~~~~~~~~~~~~~~~~

::

  tar xzf scoringengine-airgapped.tar.gz
  cd scoringengine-airgapped

3. Load Docker Images
~~~~~~~~~~~~~~~~~~~~~

::

  ./load-images.sh

Verify all images are loaded:

::

  docker images

You should see:

- ``python:3.14.1-slim-bookworm``
- ``redis:7.0.4``
- ``mariadb:10``
- ``nginx:1.23.1``
- ``scoringengine/base``
- ``scoringengine/bootstrap``
- ``scoringengine/engine``
- ``scoringengine/worker``
- ``scoringengine/web``

4. Configure Competition
~~~~~~~~~~~~~~~~~~~~~~~~~

::

  cd scoringengine

  # Edit competition configuration
  nano bin/competition.yaml

  # Edit engine configuration if needed
  nano docker/engine.conf.inc

5. Deploy Scoring Engine
~~~~~~~~~~~~~~~~~~~~~~~~~

::

  # First time deployment (creates database)
  SCORINGENGINE_OVERWRITE_DB=true docker-compose up -d

  # Subsequent starts
  docker-compose up -d

6. Verify Deployment
~~~~~~~~~~~~~~~~~~~~

::

  # Check all containers are running
  docker-compose ps

  # Check logs
  docker-compose logs -f

  # Test web interface
  curl http://localhost

Access the web interface at ``http://localhost`` or ``http://SERVER_IP``.

Default credentials (if using example mode):

- ``whiteteamuser:testpass``
- ``team1user1:testpass``
- ``team2user1:testpass``

Troubleshooting
---------------

Images Not Found
~~~~~~~~~~~~~~~~

If you get "image not found" errors:

1. Verify images are loaded: ``docker images``
2. Re-run the load script: ``./load-images.sh``
3. Check image names match docker-compose.yml

Network Issues
~~~~~~~~~~~~~~

The scoring engine creates an internal Docker network. No internet connectivity is required once images are loaded.

Database Connection Failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wait 30-60 seconds for MySQL/MariaDB to initialize on first start:

::

  docker-compose logs mysql

Storage Space
~~~~~~~~~~~~~

Ensure adequate disk space:

::

  df -h

The full deployment requires approximately 2-3 GB for images plus database growth over time.

Updates and Changes
-------------------

Making Configuration Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To update competition.yaml or other configs:

1. Stop the engine: ``docker-compose stop engine``
2. Make changes to configuration files
3. Restart: ``docker-compose start engine``

Updating Code (Requires Rebuild)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to modify the Scoring Engine code in the airgapped environment:

1. Make code changes in ``scoringengine/scoring_engine/``
2. Rebuild images: ``docker-compose build``
3. Recreate containers: ``docker-compose up -d``

.. note:: Rebuilding in airgapped mode works because all dependencies are already cached in the base image layers.

Backup and Restore
------------------

Backing Up Competition Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  # Backup database
  docker-compose exec mysql mysqldump -u se_user -pCHANGEME scoring_engine > backup.sql

  # Backup volumes
  docker run --rm -v scoringengine_mysql:/data -v $(pwd):/backup ubuntu tar czf /backup/mysql-backup.tar.gz /data

Restoring from Backup
~~~~~~~~~~~~~~~~~~~~~~

::

  # Restore database
  docker-compose exec -T mysql mysql -u se_user -pCHANGEME scoring_engine < backup.sql

Security Considerations
-----------------------

Change Default Passwords
~~~~~~~~~~~~~~~~~~~~~~~~

Before deployment, update default passwords in ``docker-compose.yml``:

::

  environment:
    - MYSQL_ROOT_PASSWORD=CHANGEME  # Change this!
    - MYSQL_PASSWORD=CHANGEME       # Change this!

Create Strong User Passwords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update user passwords in ``bin/competition.yaml`` before deployment.

Restrict Network Access
~~~~~~~~~~~~~~~~~~~~~~~~

Configure firewall rules to restrict access to the scoring engine as needed for your competition.

Additional Resources
--------------------

- Main documentation: https://scoringengine.readthedocs.io/
- GitHub repository: https://github.com/scoringengine/scoringengine
- Docker documentation: https://docs.docker.com/
- Docker Compose documentation: https://docs.docker.com/compose/

Testing the Airgapped Package
------------------------------

Before going to the competition, test your airgapped package:

1. Build and export on a system with internet
2. Copy to a test system
3. Disconnect test system from internet
4. Follow deployment steps
5. Verify all functionality works

This ensures you have everything needed before entering the airgapped environment.

Quick Reference
---------------

**Preparation (with internet):**

::

  git clone https://github.com/scoringengine/scoringengine.git
  cd scoringengine
  docker-compose build
  # Export images and create package (see steps above)

**Deployment (airgapped):**

::

  tar xzf scoringengine-airgapped.tar.gz
  cd scoringengine-airgapped
  ./load-images.sh
  cd scoringengine
  docker-compose up -d

**Management:**

::

  # View status
  docker-compose ps

  # View logs
  docker-compose logs -f

  # Stop engine
  docker-compose stop engine

  # Start engine
  docker-compose start engine

  # Stop all
  docker-compose down

  # Restart all
  docker-compose restart
