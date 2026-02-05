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
blue_team_view_status_page = True
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

# SLA Penalty Configuration
# Enable/disable SLA penalties (consecutive failure penalties)
sla_enabled = False
# Number of consecutive failures before penalties begin
sla_penalty_threshold = 5
# Penalty percentage per failure after threshold (e.g., 10 = 10%)
sla_penalty_percent = 10
# Maximum total penalty percentage (e.g., 50 = 50% max penalty)
sla_penalty_max_percent = 50
# Penalty mode: additive, flat, exponential, or next_check_reduction
# - additive: Penalty accumulates (10%, 20%, 30%...)
# - flat: Fixed penalty per failure after threshold
# - exponential: Penalty doubles each failure (5%, 10%, 20%...)
# - next_check_reduction: Next successful check worth less
sla_penalty_mode = additive
# Allow scores to go negative from penalties
sla_allow_negative = False

# Dynamic Scoring (Time-Based) Configuration
# Enable/disable dynamic scoring multipliers
dynamic_scoring_enabled = False
# Early phase: First N rounds have a multiplier applied
dynamic_scoring_early_rounds = 10
# Multiplier for early rounds (e.g., 2.0 = 2x points)
dynamic_scoring_early_multiplier = 2.0
# Late phase: After round N, different multiplier applied
dynamic_scoring_late_start_round = 50
# Multiplier for late rounds (e.g., 0.5 = 0.5x points)
dynamic_scoring_late_multiplier = 0.5
