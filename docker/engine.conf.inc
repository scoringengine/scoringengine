[GENERAL]
checks_location = scoring_engine/engine/checks
check_timeout = 30
round_time_sleep = 180
worker_refresh_time = 30
timezone = US/Eastern

[DB]
# SQLite
uri = mysql://se_user:CHANGEME@mysql/scoring_engine

[REDIS]
host = redis
port = 6379
password =
