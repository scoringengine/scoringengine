import json
import secrets
from functools import wraps

from flask import Blueprint, g, jsonify, request
from flask_login import current_user, login_required

import redis as redis_lib

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.models.notifications import Notification


def make_cache_key(*args, **kwargs):
    """Function to generate a cache key."""
    request_path = request.path
    if g.user.is_anonymous:
        return f"{request_path}_anonymous"
    if g.user.is_white_team:
        return f"{request_path}_white"
    if g.user.is_red_team:
        return f"{request_path}_red"
    return f"{request_path}_team_{g.user.team.id}"


mod = Blueprint("api", __name__)


@mod.route("/api/events/token")
def events_token():
    """Generate a short-lived token for SSE connection.

    Stores user info in Redis so the SSE server can look it up without
    sharing Flask's SECRET_KEY. Anonymous users get a public-only token.
    """
    token = secrets.token_urlsafe(32)
    if current_user.is_authenticated:
        if current_user.is_white_team:
            role = "white"
        elif current_user.is_red_team:
            role = "red"
        else:
            role = "blue"
        user_info = {
            "user_id": current_user.id,
            "team_id": current_user.team.id,
            "role": role,
        }
    else:
        user_info = {"user_id": None, "team_id": None, "role": "anonymous"}

    r = redis_lib.Redis(host=config.redis_host, port=config.redis_port, password=config.redis_password)
    r.setex(f"sse_token:{token}", 300, json.dumps(user_info))
    return jsonify({"token": token})


from . import admin, agent, announcements, flags, injects, notifications, overview, profile, scoreboard, service, sla, stats, team
