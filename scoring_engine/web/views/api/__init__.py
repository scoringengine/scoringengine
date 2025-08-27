from flask import Blueprint, g, request
from functools import wraps

from scoring_engine.cache import cache
from scoring_engine.models.notifications import Notification


def make_cache_key(*args, **kwargs):
    """Function to generate a cache key."""
    request_path = request.path
    team_id = g.user.team.id  # Assuming g.user.team is available

    # Return a unique key based on the function name and team information (user info not needed due to everything based on teams)
    return f"{request_path}_{team_id}"


mod = Blueprint("api", __name__)


from . import admin
from . import agent
from . import flags
from . import injects
from . import notifications
from . import overview
from . import profile
from . import scoreboard
from . import service
from . import stats
from . import team
