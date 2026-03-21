from celery import Celery

from scoring_engine.config import config

redis_server = "redis://:" + config.redis_password + "@" + config.redis_host + ":" + str(config.redis_port)
celery_app = Celery(
    "engine.worker", backend=redis_server, broker=redis_server + "/0", include=["scoring_engine.engine.execute_command"]
)

# Set Redis socket timeouts to fail fast instead of hanging for the
# full 120s TCP timeout when a connection goes stale.
# Broker (Kombu transport)
celery_app.conf.broker_transport_options = {
    "socket_timeout": 10,
    "socket_connect_timeout": 5,
}
# Result backend (Celery Redis backend)
celery_app.conf.redis_socket_timeout = 10
celery_app.conf.redis_socket_connect_timeout = 5
celery_app.conf.redis_retry_on_timeout = True
celery_app.conf.redis_socket_keepalive = True
# Limit Redis connection pool size to prevent connection exhaustion.
# Default is unlimited, which leads to 1000+ connections under load.
celery_app.conf.redis_max_connections = 50
