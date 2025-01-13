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
db_uri = sqlite:////tmp/test_engine.db?check_same_thread=False

worker_num_concurrent_tasks = 4
worker_queue = main

# Set to null to disable caching
cache_type = null

redis_host = 127.0.0.1
redis_port = 6379
redis_password = testpass
