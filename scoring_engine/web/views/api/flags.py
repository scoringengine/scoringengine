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

    # Serialize flags and include localized times
    data = [
        {
            "id": f.id,
            "start_time": f.localize_start_time,  # Use the localized property
            "end_time": f.localize_end_time,  # Use the localized property
            "type": f.type.value,
            "platform": f.platform.value,
            "perm": f.perm.value,
            "path": f.data.get("path"),
            "content": f.data.get("content"),
        }
        for f in flags
    ]

    return jsonify(data=data)
