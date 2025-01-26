from flask import jsonify
from flask_login import current_user, login_required


from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.team import Team
from scoring_engine.models.flag import Flag

from . import make_cache_key, mod


@mod.route("/api/flags")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags():
    team = session.query(Team).get(current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_red_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    flags = session.query(Flag).all()

    # Convert flags to dictionaries and add to response
    data = [
        {
            "id": f.id,
            "type": f.type,
            "perm": f.perm,
            "platform": f.platform,
            "start_time": f.start_time,
            "end_time": f.end_time,
            "path": f.data["path"],
            "content": f.data["content"],
        }
        for f in flags
    ]

    return jsonify(data=data)
