"""Lightweight SSE server using gevent.

Runs alongside uWSGI in the web container on port 8001.
A single background greenlet subscribes to Redis pub/sub and broadcasts
events to all connected SSE clients, filtered by each client's role/team.

Usage:
    python -m scoring_engine.sse_server
"""

from gevent import monkey

monkey.patch_all()

import json
import logging
import os
import time
from urllib.parse import parse_qs

import gevent
import redis
from gevent.event import Event
from gevent.pywsgi import WSGIServer

from scoring_engine.config import config
from scoring_engine.events import CHANNEL

logger = logging.getLogger("sse_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

# Global list of connected clients. Each entry is a dict with:
#   "role", "team_id", "queue" (gevent.queue.Queue)
_clients = []
_clients_lock = gevent.lock.RLock()


def _get_redis():
    return redis.Redis(host=config.redis_host, port=config.redis_port, password=config.redis_password)


def _validate_token(token):
    """Look up SSE token in Redis. Returns user_info dict or None."""
    if not token:
        return None
    r = _get_redis()
    data = r.get(f"sse_token:{token}")
    if data is None:
        return None
    r.expire(f"sse_token:{token}", 300)
    return json.loads(data)


def should_send_event(event, role, team_id):
    """Determine if an event should be sent to a client based on visibility."""
    vis = event.get("visibility", "public")
    if vis == "public":
        return True
    if role == "white":
        return True
    if vis == "blue" and role == "blue" and event.get("team_id") == team_id:
        return True
    if vis == "red" and role == "red":
        return True
    return False


def _redis_listener():
    """Background greenlet: subscribe to Redis and broadcast to all clients."""
    while True:
        try:
            r = _get_redis()
            pubsub = r.pubsub()
            pubsub.subscribe(CHANNEL)
            logger.info("Redis listener subscribed to %s", CHANNEL)

            for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    event = json.loads(message["data"])
                except (json.JSONDecodeError, KeyError):
                    continue

                with _clients_lock:
                    for client in _clients:
                        if should_send_event(event, client["role"], client["team_id"]):
                            try:
                                client["queue"].put_nowait(event)
                            except gevent.queue.Full:
                                pass  # Drop events for slow clients

        except Exception as e:
            logger.warning("Redis listener error: %s, reconnecting in 1s", e)
            gevent.sleep(1)


def handle_sse(environ, start_response):
    """WSGI app that handles SSE connections."""
    path = environ.get("PATH_INFO", "")

    if path == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    if path != "/api/events":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not found"]

    qs = parse_qs(environ.get("QUERY_STRING", ""))
    token = qs.get("token", [None])[0]
    user_info = _validate_token(token)
    if user_info is None:
        start_response("401 Unauthorized", [("Content-Type", "text/plain")])
        return [b"Invalid or expired token"]

    role = user_info.get("role", "anonymous")
    team_id = user_info.get("team_id")

    logger.info("SSE client connected: role=%s team_id=%s", role, team_id)

    headers = [
        ("Content-Type", "text/event-stream"),
        ("Cache-Control", "no-cache"),
        ("Connection", "keep-alive"),
        ("X-Accel-Buffering", "no"),
    ]
    start_response("200 OK", headers)

    client = {
        "role": role,
        "team_id": team_id,
        "queue": gevent.queue.Queue(maxsize=50),
    }

    with _clients_lock:
        _clients.append(client)

    def event_stream():
        try:
            yield b":\n\n"  # Initial heartbeat
            last_heartbeat = time.time()

            while True:
                try:
                    event = client["queue"].get(timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n".encode()
                except gevent.queue.Empty:
                    pass

                now = time.time()
                if now - last_heartbeat >= 15:
                    yield b":\n\n"
                    last_heartbeat = now

        except GeneratorExit:
            pass
        finally:
            logger.info("SSE client disconnected: role=%s team_id=%s", role, team_id)
            with _clients_lock:
                if client in _clients:
                    _clients.remove(client)

    return event_stream()


def main():
    port = int(os.environ.get("SSE_PORT", 8001))

    # Start Redis listener in background
    gevent.spawn(_redis_listener)

    logger.info("Starting SSE server on port %d", port)
    server = WSGIServer(("0.0.0.0", port), handle_sse, log=logger)
    server.serve_forever()


if __name__ == "__main__":
    main()
