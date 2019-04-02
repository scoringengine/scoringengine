Docker
======

.. note:: It takes a minute or 2 for all of the containers to start up and get going!

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

