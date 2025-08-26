[OPTIONS]
checks_location = scoring_engine/checks
target_round_time = 180
worker_refresh_time = 30
engine_paused = False
pause_duration = 30
timezone = US/Eastern
upload_folder = /var/uploads

debug = False

# Use a lightweight SQLite database for integration tests
db_uri = sqlite:///integration_test.db

worker_num_concurrent_tasks = -1
worker_queue = main

# Disable caching for tests
cache_type = null

# Redis configuration is unnecessary when caching is disabled
# redis_host = redis
# redis_port = 6379
# redis_password =
