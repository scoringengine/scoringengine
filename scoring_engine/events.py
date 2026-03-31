"""Server-Sent Events publishing via Redis pub/sub.

The engine and web containers publish events to a single Redis channel.
The SSE server subscribes and streams matching events to connected clients.
"""

import json

import redis

from scoring_engine.config import config

CHANNEL = "se:events"


def should_send_event(event, role, team_id):
    """Determine if an event should be sent to a client based on visibility.

    Parameters
    ----------
    event : dict
        Event with "visibility" and optionally "team_id" keys.
    role : str
        Client role: "anonymous", "blue", "red", or "white".
    team_id : int or None
        Client's team ID (for blue team filtering).
    """
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

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password,
        )
    return _redis_client


def publish_event(event_type, data=None, visibility="public", team_id=None):
    """Publish an event to Redis pub/sub.

    Parameters
    ----------
    event_type : str
        Event name, e.g. "round_complete", "inject_update", "announcement".
    data : dict, optional
        Small payload (clients re-fetch from API, so keep this minimal).
    visibility : str
        "public" (everyone), "white", "red", or "blue" (requires team_id).
    team_id : int, optional
        Required when visibility="blue" to target a specific team.
    """
    message = json.dumps(
        {
            "type": event_type,
            "data": data or {},
            "visibility": visibility,
            "team_id": team_id,
        }
    )
    try:
        _get_redis().publish(CHANNEL, message)
    except Exception:
        # Publishing is best-effort — don't break the caller
        pass
