[OPTIONS]
checks_location = scoring_engine/checks
round_time_sleep = 180
worker_refresh_time = 30
timezone = US/Eastern

debug = False

# SQLite
db_uri = sqlite:////tmp/test_engine.db

# Set to -1 to use default number of processors for tasks
# else, set to number of concurrent tasks
worker_num_concurrent_tasks = 4

# Set to null to disable caching
cache_type = null

redis_host = 127.0.0.1
redis_port = 6379
redis_password = testpass
