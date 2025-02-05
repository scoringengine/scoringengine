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
.. note:: Each of these config keys can be expressed via environment variables (and take precendence over the values defined in the file). IE: To define target_round_time, I'd set SCORINGENGINE_TARGET_ROUND_TIME=3.

.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Key Name
     - Description
   * - checks_location
     - Local path to directory of checks
   * - target_round_time
     - Length of time (seconds) the engine should target per round
   * - agent_psk
     - The pre-shared key used for encryption between BTA and the Scoring Engine
   * - agent_show_flag_early_mins
     - The length of time in minutes before a flag becomes active that BTA can grab the flag details
   * - worker_refresh_time
     - Amount of time (seconds) the engine will sleep for in-between polls of worker status
   * - worker_num_concurrent_tasks
     - The number of concurrent tasks the worker will run. Set to -1 to default to number of processors.
   * - worker_queue
     - The queue name for a worker to pull tasks from. This can be used to control which workers get which service checks. Default is 'main'
   * - blue_team_update_hostname
     - A boolean indicating if blue teams should be allowed to update the hostnames associated for scored checks
   * - blue_team_update_port
     - A boolean indicating if blue teams should be allowed to update the port associated for scored checks
   * - blue_team_update_account_usernames
     - A boolean indicating if blue teams should be allowed to change usernames associated with scored checks
   * - blue_team_update_account_passwords
     - A boolean indicating if blue teams should be allowed to change passwords of scored users
   * - blue_team_view_check_output
     - A boolean indicating if blue teams should be allowed to view verbose output from checks
   * - timezone
     - Local timezone of the competition
   * - debug
     - Determines wether or not the engine should be run in debug mode (useful for development). The worker will also display output from all checks.
   * - db_uri
     - Database connection URI
   * - cache_type
     - The type of storage for the cache. Set to null to disable caching
   * - redis_host
     - The hostname/ip of the redis server
   * - redis_port
     - The port of the redis server
   * - redis_password
     - The password used to connect to redis (if no password, leave empty)
