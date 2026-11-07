[OPTIONS]
checks_location = scoring_engine/checks
target_round_time = 180
agent_psk = TheCakeIsALie
agent_show_flag_early_mins = 5
worker_refresh_time = 30
# How many rounds may fail back to back before the engine gives up and exits
# non-zero.  A failed round (usually a database blip) is rolled back and
# retried, but an error that reproduces every round is not transient: the
# engine exits so the container restart is visible to the operator instead of
# it silently spinning through the competition producing no rounds.
# Set to 0 to retry forever (not recommended).
max_consecutive_round_failures = 3
engine_paused = False
pause_duration = 30
blue_team_update_hostname = True
blue_team_update_port = True
blue_team_update_account_usernames = True
blue_team_update_account_passwords = True
blue_team_view_check_output = True
anonymize_team_names = True
timezone = US/Eastern
upload_folder = /var/uploads
check_output_folder = /var/check_outputs

debug = False

# Flask session signing key for the web application.
#
# MUST be set to a long, random value and MUST stay the same across restarts
# and across every web process/container:
#   * If it changes, all session cookies become invalid and every user is
#     logged out.
#   * If two web processes/containers hold different keys, a session created
#     by one is rejected by the other, so you cannot run more than one web
#     replica behind a load balancer.
#
# Left empty on purpose -- no default key is shipped, because a fixed default
# would let anyone forge session cookies. If it is empty the web app still
# starts, but generates a throwaway key and logs a warning.
#
# Generate one with:
#   python -c "import secrets; print(secrets.token_hex(64))"
secret_key =

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

# Tool packs installed on this worker: core, db, rdp, browser, adcs. The worker
# consumes "<worker_queue>" for core and "<worker_queue>.<pack>" for the rest.
# Docker worker images set this automatically (SCORINGENGINE_WORKER_PACKS).
worker_packs = core,db,rdp,browser,adcs

# Maximum random delay (in seconds) added to each task before workers
# pick it up. Spreads checks across the round window so workers don't
# all hit target services at the same instant. 0 = disabled (all tasks
# dispatched immediately). A good starting value is ~1/6 of
# target_round_time (e.g. 30 for a 180s round).
task_jitter_max_delay = 0

# Set to null to disable caching
cache_type = redis

redis_host = 127.0.0.1
redis_port = 6379
redis_password =

# Mark the session and remember-me cookies "Secure" so the browser only ever
# sends them over HTTPS.  Set this to True for any deployment served over TLS
# (the bundled docker compose stack terminates TLS at nginx and already sets
# it).  Leave it False for a plain-HTTP dev run, otherwise the browser will
# drop the session cookie and logins will appear to do nothing.
session_cookie_secure = False

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

# Inject Score Visibility
# Show inject scores on the public scoreboard (default: hidden for private grading)
inject_scores_visible = False

# Red-Team Flag Scoring
# Flat points awarded to the red team per captured flag, by permission level.
# A captured flag (a Solve reported by a blue team's agent) adds to the red
# team's total; the compromised blue team's own score is not reduced.
flag_points_user = 100
flag_points_root = 200

# Weighted Scoring
# Rebalance how service uptime, injects, and flag captures combine into the
# scoreboard total (e.g. dampen flags if they dominate, or make injects count
# for more). Each weight is a multiplier; disabled means every weight is
# effectively 1.0 and totals are unchanged.
weighted_scoring_enabled = False
service_weight = 1.0
inject_weight = 1.0
flag_weight = 1.0
