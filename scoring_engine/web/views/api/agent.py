from flask import jsonify, request, abort
from flask_login import current_user, login_required
from sqlalchemy import desc, func, exists
from sqlalchemy.sql.expression import and_
from datetime import datetime, timedelta
from typing import Tuple

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.flag import Flag, Solve, Platform
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.setting import Setting

from . import mod


@mod.route("/api/agent/flags")
def agent_show_flags():
    now = datetime.utcnow()
    # show upcoming flags a little bit early so red team can plant them
    # and implants that might stop checking in still get the next set of flags
    early = now + timedelta(
        minutes=int(Setting.get_setting("agent_show_flag_early_mins").value)
    )
    flags = (
        session.query(Flag)
        .filter(and_(early > Flag.start_time, now < Flag.end_time))
        .all()
    )
    return jsonify([flag.as_dict() for flag in flags])


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
        team: Team = session.query(Team).get(int(request.args["team"]))
        host = request.args["host"]
        platform = Platform(request.args["plat"])
    except (ValueError, KeyError):
        abort(400)
    if team is None or host is None:
        abort(400)
    if not team.is_blue_team:
        abort(400)
    return team, host, platform


def do_checkin(team, host, platform):
    now = datetime.utcnow()
    # show upcoming flags a little bit early so red team can plant them
    # and implants that might stop checking in still get the next set of flags
    early = now + timedelta(
        minutes=int(Setting.get_setting("agent_show_flag_early_mins").value)
    )
    # get unsolved flags for this team and host and for this time period
    flags = (
        session.query(Flag)
        .filter(
            and_(
                Flag.platform == platform,
                early > Flag.start_time,
                now < Flag.end_time,
            )
        )
        .filter(
            ~exists().where(
                and_(Flag.id == Solve.flag_id, Solve.team == team, Solve.host == host)
            )
        )
        .all()
    )

    res = {
        "flags": [f.as_dict() for f in flags],
        "config": {
            "checkin_interval": {
                "secs": int(Setting.get_setting("agent_checkin_interval_sec").value),
                "nanos": 0,
            }
        },
        "timestamp": int(datetime.utcnow().timestamp()),
    }
    return jsonify(res)
