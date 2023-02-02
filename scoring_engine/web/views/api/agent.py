from flask import jsonify, request, abort
from flask_login import current_user, login_required
from sqlalchemy import desc, func, exists
from sqlalchemy.sql.expression import and_
from datetime import datetime
from typing import Tuple

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.flag import Flag, Solve, Platform
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import mod


cache_dict = {}  # TODO - This is a dev hack. Real users should be using the flask-caching cache to store values


@mod.route("/api/agent/checkin")
def agent_checkin_get():
    return do_checkin(*get_host_info())


@mod.route("/api/agent/checkin", methods=["POST"])
def agent_checkin_post():
    data = request.get_json()
    team, host, platform = get_host_info()
    flags = data.get("flags", [])
    flags = session.query(Flag).filter(Flag.id.in_(flags)).all()
    solves = [
        Solve(
            host=host,
            team=team,
            flag=flag,
        )
        for flag in flags
    ]
    session.add_all(solves)
    return do_checkin(team, host, platform)


def get_host_info() -> Tuple[Team, str, Platform]:
    try:
        team = session.query(Team).get(int(request.args["team"]))
        host = request.args["host"]
        platform = Platform(request.args["plat"])
    except (ValueError, KeyError):
        abort(400)
    if team is None or host is None:
        abort(400)
    return team, host, platform


def do_checkin(team, host, platform):
    now = datetime.utcnow()
    # get unsolved flags for this team and host and for this time period
    flags = (
        session.query(Flag)
        .filter(
            and_(Flag.platform == platform, now > Flag.start_time, now < Flag.end_time)
        )
        .filter(~exists().where(and_(Solve.team == team, Solve.host == host)))
        .all()
    )

    res = {
        "flags": [f.as_dict() for f in flags],
        "config": None,
        "timestamp": int(datetime.utcnow().timestamp()),
    }

    # TODO - this is a gross dev hack
    if cache.config['CACHE_TYPE'] == 'null':
        cache_dict[host] = now
        # print(cache_dict)
    else:
        cache.set(host, res)
        # print(cache.get(host))

    return jsonify(res)
