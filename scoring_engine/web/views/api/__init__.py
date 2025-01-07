from flask import Blueprint

from scoring_engine.models.notifications import Notification

from functools import wraps
from flask import g
from scoring_engine.cache import cache


def make_cache_key(*args, **kwargs):
    """Function to generate a cache key."""
    # Access the function name and user/team information
    fn_name = kwargs.get("fn").__name__  # Access the function name dynamically
    user_id = g.user.id  # Assuming g.user is set
    team_id = g.user.team.id  # Assuming g.user.team is available

    # Return a unique key based on the function name and user/team information
    return f"{fn_name}_{team_id}_{user_id}"


mod = Blueprint("api", __name__)


from . import admin
from . import agent
from . import injects
from . import notifications
from . import overview
from . import profile
from . import scoreboard
from . import service
from . import stats
from . import team
