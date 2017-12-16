Docker
======

.. note:: It takes a minute or 2 for all of the containers to start up and get going!

TestBed Environment
-------------------
::

  make rebuild-testbed-new

This command will build, stop any pre-existing scoring engine containers, and start a new environment. As part of the environment, multiple containers will be used as part of the testbed environment.




Production Environment
----------------------

Modify the bin/populate_db script to configure the engine according to your competition environment. Then, run the following make command to build, and run the scoring engine.

.. warning:: This will delete the previous database, exclude the 'new' part from the command to not rebuild the db.

::

  make rebuild-new

Then, to 'pause' the scoring engine (Ex: At the end of the day)::

  docker-compose -f docker-compose.yml stop engine

To 'unpause' the engine::

  docker-compose -f docker-compose.yml start engine

