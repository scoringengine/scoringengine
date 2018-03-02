[GENERAL]
checks_location = scoring_engine/engine/checks
round_time_sleep = 180
worker_refresh_time = 30
timezone = US/Eastern

[WEB]
debug = False

[DB]
# SQLite
uri = sqlite:////tmp/engine.db
# MySQL
#uri = mysql://user:password@host/database?charset=utf8mb4
# Postgresql
#uri = postgresql://user:password@host/database

[CACHE]
# Set to null to disable caching
cache_type = redis

[REDIS]
host = 127.0.0.1
port = 6379
password =
