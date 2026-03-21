from functools import wraps

from flask import Blueprint, g, request

from scoring_engine.cache import cache
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


from . import admin, agent, announcements, flags, injects, notifications, overview, profile, scoreboard, service, sla, stats, team
