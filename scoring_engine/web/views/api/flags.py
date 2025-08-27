from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, case
from sqlalchemy.sql.expression import and_, or_

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.flag import Flag, Solve
from scoring_engine.models.setting import Setting

from datetime import datetime, timedelta

from . import make_cache_key, mod


@mod.route("/api/flags")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags():
    team = session.get(Team, current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_red_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    now = datetime.utcnow()
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    flags = (
        session.query(Flag).filter(and_(early > Flag.start_time, now < Flag.end_time, Flag.dummy == False)).order_by(Flag.start_time).all()
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
    if not current_user.is_red_team and not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    # Get all flags and teams
    now = datetime.utcnow()
    active_flags = session.query(Flag).filter(and_(now > Flag.start_time, now < Flag.end_time, Flag.dummy == False)).order_by(Flag.start_time).all()
    active_flag_ids = [flag.id for flag in active_flags]

    # Flag Solve Status
    all_hosts = session.query(Service.name.label("service_name"), Service.port, Service.team_id, Service.host, Team.name.label("team_name"), func.coalesce(Solve.id, None).label("solve_id"), func.coalesce(Flag.id, None).label("flag_id"), func.coalesce(Flag.perm, None).label("flag_perm"), func.coalesce(Flag.platform, None).label("flag_platform")).select_from(Service).filter(Service.check_name == "AgentCheck").outerjoin(Solve, and_(Solve.host == Service.host, Solve.team_id == Service.team_id, Solve.flag_id.in_(active_flag_ids))).outerjoin(Flag, Flag.id == Solve.flag_id).outerjoin(Team, Team.id == Service.team_id).order_by(Service.name, Service.team_id).all()

    data = {}
    rows = []
    columns = ["Team"]

    for item in all_hosts:
        if item.service_name not in columns:
            columns.append(item.service_name)
        if not data.get(item.team_name):
            data[item.team_name] = {}
        if not data[item.team_name].get(item.service_name):
            data[item.team_name][item.service_name] = [0, 0]
        if item.solve_id:
            if item.flag_perm.value == "user":
                data[item.team_name][item.service_name][0] = 1
            else:
                data[item.team_name][item.service_name][1] = 1

    for key, val in data.items():
        new_row = [key]
        for host in val.values():
            new_row.append(host)
        rows.append(new_row)

    return jsonify(data={"columns": columns, "rows": rows})

@mod.route("/api/flags/totals")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags_totals():
    if not current_user.is_red_team and not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    totals = {}  # [ Team0, Win Score, Nix Score ]
    blue_teams = ( session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all() )
    for blue_team in blue_teams:
        totals[blue_team.name] = [blue_team.name, 0, 0]

    for platform in ["windows", "nix"]:
        # Subquery 1: Determine permission level
        subquery1 = (
            session.query(
                Solve.team_id,
                Flag.platform,
                Solve.host,
                func.if_(
                    func.group_concat(func.distinct(Flag.perm), ',') == "user,root",
                    "root",
                    func.group_concat(func.distinct(Flag.perm))
                ).label("level")
            )
            .join(Flag, Flag.id == Solve.flag_id)
            .filter(Flag.platform.like(platform))
            .group_by(Solve.team_id, Flag.platform, Solve.host, Flag.start_time)
            .subquery()
        )
        
        # Subquery 2: Compute red_amt based on level
        subquery2 = (
            session.query(
                (subquery1.c.team_id).label("BlueTeamId"),
                case(
                    (subquery1.c.level.like("user"), 0.5 * func.count()),
                    else_=1 * func.count()
                ).label("red_amt")
            )
            .group_by(subquery1.c.team_id, subquery1.c.level)
            .order_by(subquery1.c.team_id, subquery1.c.level.desc())
            .subquery()
        )
        
        # Final Query: Sum red_amt per BlueTeamId
        final_query = (
            session.query(
                Team.name.label("BlueTeam"),
                func.sum(subquery2.c.red_amt).label("RedScore")
            )
            .join(Team, subquery2.c.BlueTeamId == Team.id)
            .group_by(subquery2.c.BlueTeamId)
            .order_by(func.sum(subquery2.c.red_amt))
        )
        
        # Execute Query
        results = final_query.all()
        
        # Print Results
        for row in results:
            if platform == "windows":
                totals[row.BlueTeam][1] = row.RedScore
            elif platform == "nix":
                totals[row.BlueTeam][2] = row.RedScore

    data = []
    for team in totals.values():
        data.append({"team": team[0], "win_score": team[1], "nix_score": team[2], "total_score": team[1] + team[2]})

    return jsonify(data=data)
