[GENERAL]
checks_location = scoring_engine/engine/checks
round_time_sleep = 180
worker_refresh_time = 30
timezone = US/Eastern

[WEB]
debug = False

[DB]
uri = sqlite:////tmp/test_engine.db

[CACHE]
# Set to null to disable caching
cache_type = null

[REDIS]
host = 127.0.0.1
port = 6379
password = testpass
