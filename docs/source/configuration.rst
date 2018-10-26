Configuration
*************

Location to config file
-----------------------
Docker
^^^^^^
.. note:: This file needs to be edited before running the make commands.

::

  <path to source root>/docker/engine.conf.inc

Manual
^^^^^^
.. note:: Need to restart each scoring engine service once the config is modified.

::

  /home/engine/scoring_engine/src/engine.conf


Config Keys
-----------
.. note:: Each of these config keys can be expressed via environment variables (and take precendence over the values defined in the file). IE: To define round_time_sleep, I'd set SCORINGENGINE_ROUND_TIME_SLEEP=3.

General
^^^^^^^
checks_location
  - The local path to the source code for checks
round_time_sleep
  - The amount of time in seconds we sleep inbetween rounds
worker_refresh_time
  - The amount of time the engine will sleep for inbetween polls of worker status
timezone
  - The timezone of the web interface

Web
^^^
debug
  - If production, set to False, else set to True. This field determines if flask should autoload edited files and such (useful in development)

DB
^^
uri
  - The full database uri

WORKER
^^^^^^
num_concurrent_tasks
  - The number of concurrent tasks the worker will run. Set to -1 to default to number of processors.

CACHE
^^^^^
cache_type
  - The type of storage for the cache. Set to null to disable caching

REDIS
^^^^^
host
  - The hostname/ip of the redis server
port
  - The port of the redis server
password
  - The password used to connect to redis (if no password, leave empty)
