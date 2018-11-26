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


Configuration Keys
------------------
.. note:: Each of these config keys can be expressed via environment variables (and take precendence over the values defined in the file). IE: To define round_time_sleep, I'd set SCORINGENGINE_ROUND_TIME_SLEEP=3.

.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Key Name
     - Description
   * - checks_location
     - Local path to directory of checks
   * - round_time_sleep
     - Amount of time (seconds) the engine sleeps between rounds
   * - worker_refresh_time
     - Amount of time (seconds) the engine will sleep for in-between polls of worker status
   * - timezone
     - Local timezone of the competition
   * - debug
     - Determines wether or not the engine should be run in debug mode (useful for development)
   * - db_uri
     - Database connection URI
   * - worker_num_concurrent_tasks
     - The number of concurrent tasks the worker will run. Set to -1 to default to number of processors.
   * - cache_type
     - The type of storage for the cache. Set to null to disable caching
   * - redis_host
     - The hostname/ip of the redis server
   * - redis_port
     - The port of the redis server
   * - redis_password
     - The password used to connect to redis (if no password, leave empty)
