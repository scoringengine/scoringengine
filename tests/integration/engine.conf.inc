[OPTIONS]
checks_location = scoring_engine/checks
target_round_time = 180
agent_psk = TheCakeIsALie
agent_show_flag_early_mins = 5
worker_refresh_time = 30
engine_paused = False
pause_duration = 30
blue_team_update_hostname = True
blue_team_update_port = True
blue_team_update_account_usernames = True
blue_team_update_account_passwords = True
blue_team_view_check_output = True
timezone = US/Eastern
upload_folder = /var/uploads

debug = False

db_uri = mysql://se_user:CHANGEME@mysql/scoring_engine?charset=utf8mb4

worker_num_concurrent_tasks = -1
worker_queue = main

# Set to null to disable caching
cache_type = redis

redis_host = redis
redis_port = 6379
redis_password =
