[OPTIONS]
checks_location = scoring_engine/checks
target_round_time = 180
worker_refresh_time = 30
engine_paused = False
pause_duration = 30
timezone = US/Eastern
upload_folder = /var/uploads

debug = False

# SQLite
db_uri = sqlite:////tmp/engine.db?check_same_thread=False
# MySQL
#db_uri = mysql://user:password@host/database?charset=utf8mb4
# Postgresql
#db_uri = postgresql://user:password@host/database

# Set to -1 to use default number of processors for tasks
# else, set to number of concurrent tasks
worker_num_concurrent_tasks = -1

# default to main
# but this allows you to have some workers
# running certain work but not others
worker_queue = main

# Set to null to disable caching
cache_type = redis

redis_host = 127.0.0.1
redis_port = 6379
redis_password =
