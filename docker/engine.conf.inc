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
timezone = US/Eastern
upload_folder = /var/uploads

debug = False

# Flask session signing key for the web application.
#
# MUST be set to a long, random value and MUST stay the same across restarts
# and across every web process/container:
#   * If it changes, all session cookies become invalid and every user is
#     logged out.
#   * If two web processes/containers hold different keys, a session created
#     by one is rejected by the other, so you cannot scale the web service
#     past a single replica.
#
# Left empty on purpose -- no default key is shipped, because a fixed default
# would let anyone forge session cookies. If it is empty the web app still
# starts, but generates a throwaway key and logs a warning.
#
# Under docker compose this file is baked into the image at build time, so the
# recommended way to set this is SCORINGENGINE_SECRET_KEY in your .env file
# (see .env.example). Generate one with:
#   python -c "import secrets; print(secrets.token_hex(64))"
secret_key =

db_uri = mysql://se_user:CHANGEME@mysql/scoring_engine?charset=utf8mb4

# Set to -1 to use default number of processors for tasks
# else, set to number of concurrent tasks
worker_num_concurrent_tasks = -1

# default to main
# but this allows you to have some workers
# running certain work but not others
worker_queue = main

# Tool packs installed on this worker: core, db, rdp, browser. The worker
# consumes "<worker_queue>" for core and "<worker_queue>.<pack>" for the rest.
# Docker worker images set this automatically (SCORINGENGINE_WORKER_PACKS).
worker_packs = core,db,rdp,browser

# Set to null to disable caching
cache_type = redis

redis_host = redis
redis_port = 6379
redis_password =

# nginx terminates TLS in front of the web container and 301s port 80 to 443,
# so the session/remember-me cookies are always sent over HTTPS here.
session_cookie_secure = True
