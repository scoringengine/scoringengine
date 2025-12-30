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
     - Pre-shared key used for the optional Black Team Agent integration. When omitted the module is disabled and the admin status page will note that configuration is required to enable it.
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
     - The type of storage for the cache. Set to ``null`` to disable caching. When enabled additional Redis settings must be provided.
   * - redis_host
     - The hostname/ip of the redis server (required when caching is enabled)
   * - redis_port
     - The port of the redis server (required when caching is enabled)
   * - redis_password
     - The password used to connect to redis (if no password, leave empty)

Optional Modules
----------------

Several capabilities are considered non-core and are disabled unless they are explicitly configured. The engine surfaces their status in three places:

* During startup the log stream will highlight missing values for optional modules.
* The admin portal status page lists each module along with whether it is enabled and ready.
* The documentation in this section identifies which configuration keys are required for each module.

Currently the optional modules are:

* **Black Team Agent** – requires ``agent_psk`` and ``agent_show_flag_early_mins``. Without these values the agent API remains disabled.
* **Redis Cache** – requires ``cache_type`` to be set to a Redis backend along with ``redis_host`` and ``redis_port``.
