from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import case, func
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.sql.expression import and_

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.team import Team
from scoring_engine.models.flag import Flag, Solve
from scoring_engine.models.setting import Setting

from datetime import datetime, timedelta

from . import make_cache_key, mod


@mod.route("/api/flags")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags():
    team = session.query(Team).get(current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_red_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    now = datetime.utcnow()
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    flags = (
        session.query(Flag).filter(and_(early > Flag.start_time, now < Flag.end_time)).order_by(Flag.start_time).all()
    )

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


@mod.route("/api/flags/solves")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags_solves():
    # team = session.query(Team).get(current_user.team.id)
    # if team is None or not current_user.team == team or not (current_user.is_red_team or current_user.is_white_team):
    #     return jsonify({"status": "Unauthorized"}), 403

    # Build a dynamic case query for each team
    columns = [Flag.id.label("flag_id")]

    # Get all flags and teams
    # all_flags = session.query(Flag.id).all()
    all_teams = Team.get_all_blue_teams()

    for team in all_teams:
        columns.append(func.max(case((Solve.team_id == team.id, True), else_=False)).label(f"{team.name}"))

    # Query to pivot the data
    now = datetime.utcnow()
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    results = (
        session.query(*columns)
        .order_by(Flag.start_time)
        .outerjoin(Solve, Solve.flag_id == Flag.id)
        .filter(and_(early > Flag.start_time, now < Flag.end_time))
        .group_by(Flag.id)
        .all()
    )

    data = [tuple(row) for row in results]

    return jsonify(data=data)
