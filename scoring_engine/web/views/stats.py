from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required
from sqlalchemy import desc
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.db import session

import pytz

mod = Blueprint("stats", __name__)


@mod.route("/stats")
@cache.memoize()
@login_required
def home():
    team = session.query(Team).get(current_user.team.id)
    if (
        team is None
        or not current_user.team == team
        # or not (current_user.is_blue_team or current_user.is_red_team)
        or not (current_user.is_blue_team)
    ):
        return jsonify({"status": "Unauthorized"}), 403

    # TODO - Move this to an API
    stats = []
    res = session.query(Check.round_id, func.min(Check.completed_timestamp), func.max(Check.completed_timestamp)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
    for row in res:
        # TODO - There's probably a better way to do this.
        num_up_services, num_down_services = Round.get_round_stats(current_user.team.id, row[0])
        stats.append(
            {
                "round_id": row[0],
                "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                "total_seconds": (row[2] - row[1]).seconds,
                "num_up_services": num_up_services,
                "num_down_services": num_down_services,
            }
        )
    return render_template("stats.html", stats=stats)
