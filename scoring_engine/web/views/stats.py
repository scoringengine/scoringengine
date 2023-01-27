from flask import Blueprint, render_template
from sqlalchemy import desc
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.models.check import Check
from scoring_engine.db import session

import pytz

mod = Blueprint("stats", __name__)


@mod.route("/stats")
@cache.memoize()
def home():
    # TODO - Move this to an API
    stats = []
    res = session.query(Check.round_id, func.min(Check.completed_timestamp), func.max(Check.completed_timestamp)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
    for row in res:
        stats.append(
            {
                "round_id": row[0],
                "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                "total_seconds": (row[2] - row[1]).seconds,
            }
        )
    return render_template("stats.html", stats=stats)
