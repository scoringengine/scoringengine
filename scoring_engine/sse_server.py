"""Lightweight SSE server using gevent.

Runs alongside uWSGI in the web container on port 8001.
Subscribes to Redis pub/sub and streams events to connected clients,
filtering by each client's role and team.

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
from gevent.pywsgi import WSGIServer

from scoring_engine.config import config
from scoring_engine.events import CHANNEL

logger = logging.getLogger("sse_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


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
    # Extend TTL on successful lookup so long-lived connections stay valid
    r.expire(f"sse_token:{token}", 300)
    return json.loads(data)


def should_send_event(event, role, team_id):
    """Determine if an event should be sent to a client based on visibility."""
    vis = event.get("visibility", "public")
    if vis == "public":
        return True
    if role == "white":
        return True  # White team sees everything
    if vis == "blue" and role == "blue" and event.get("team_id") == team_id:
        return True
    if vis == "red" and role == "red":
        return True
    return False


def handle_sse(environ, start_response):
    """WSGI app that handles SSE connections."""
    path = environ.get("PATH_INFO", "")

    # Health check
    if path == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    # Only handle /api/events
    if path != "/api/events":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not found"]

    # Parse token from query string
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

    class SSEStream:
        """Iterator that yields SSE events from Redis pub/sub."""

        def __init__(self):
            self.pubsub = _get_redis().pubsub()
            self.pubsub.subscribe(CHANNEL)
            self.closed = False

        def __iter__(self):
            return self

        def __next__(self):
            if self.closed:
                raise StopIteration

            last_heartbeat = time.time()
            while not self.closed:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        if should_send_event(event, role, team_id):
                            return f"data: {json.dumps(event)}\n\n".encode()
                    except (json.JSONDecodeError, KeyError):
                        pass

                # Heartbeat every 15s to keep connection alive
                now = time.time()
                if now - last_heartbeat >= 15:
                    last_heartbeat = now
                    return b":\n\n"

            raise StopIteration

        def close(self):
            self.closed = True
            logger.info("SSE client disconnected: role=%s team_id=%s", role, team_id)
            try:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            except Exception:
                pass

    # Send initial heartbeat
    stream = SSEStream()
    return itertools_chain([b":\n\n"], stream)


def itertools_chain(first, rest):
    """Yield from first, then from rest."""
    yield from first
    yield from rest


def main():
    port = int(os.environ.get("SSE_PORT", 8001))
    logger.info("Starting SSE server on port %d", port)
    server = WSGIServer(("0.0.0.0", port), handle_sse, log=logger)
    server.serve_forever()


if __name__ == "__main__":
    main()
