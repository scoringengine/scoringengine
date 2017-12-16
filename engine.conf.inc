[GENERAL]
# The local path to the source code for checks
checks_location = scoring_engine/engine/checks
# The maximum time a check will run for before it times out
check_timeout = 30
# The amount of time in seconds we sleep inbetween rounds
round_time_sleep = 180
# The amount of time the engine will sleep for inbetween polls of worker status
worker_refresh_time = 30
# The timezone of the web interface
timezone = US/Eastern

[WEB]
# If production, set to False
debug = False

[DB]
# SQLite
uri = sqlite:////tmp/engine.db
# MySQL
#uri = mysql://user:password@host/database
# Postgresql
#uri = postgresql://user:password@host/database

[REDIS]
host = 127.0.0.1
port = 6379
password =
