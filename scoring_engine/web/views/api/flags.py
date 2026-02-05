from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, case
from sqlalchemy.sql.expression import and_, or_

from scoring_engine.cache import cache
from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.flag import Flag, Solve
from scoring_engine.models.setting import Setting

from datetime import datetime, timedelta, timezone

from . import make_cache_key, mod


@mod.route("/api/flags")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_flags():
    team = db.session.get(Team, current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_red_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    # Use naive UTC time for SQLAlchemy filter comparison (databases may not support timezones)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    flags = (
        db.session.query(Flag).filter(and_(early > Flag.start_time, now < Flag.end_time, Flag.dummy == False)).order_by(Flag.start_time).all()
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
    # Use naive UTC time for SQLAlchemy filter comparison (databases may not support timezones)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    active_flags = db.session.query(Flag).filter(and_(now > Flag.start_time, now < Flag.end_time, Flag.dummy == False)).order_by(Flag.start_time).all()
    active_flag_ids = [flag.id for flag in active_flags]

    # Flag Solve Status
    all_hosts = db.session.query(Service.name.label("service_name"), Service.port, Service.team_id, Service.host, Team.name.label("team_name"), func.coalesce(Solve.id, None).label("solve_id"), func.coalesce(Flag.id, None).label("flag_id"), func.coalesce(Flag.perm, None).label("flag_perm"), func.coalesce(Flag.platform, None).label("flag_platform")).select_from(Service).filter(Service.check_name == "AgentCheck").outerjoin(Solve, and_(Solve.host == Service.host, Solve.team_id == Service.team_id, Solve.flag_id.in_(active_flag_ids))).outerjoin(Flag, Flag.id == Solve.flag_id).outerjoin(Team, Team.id == Service.team_id).order_by(Service.name, Service.team_id).all()

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

    # Initialize totals for all blue teams: {team_name: [team_name, win_score, nix_score]}
    totals = {}
    blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    team_id_to_name = {}
    for blue_team in blue_teams:
        totals[blue_team.name] = [blue_team.name, 0.0, 0.0]
        team_id_to_name[blue_team.id] = blue_team.name

    # Fetch all solves with their flags in one query
    solves = (
        db.session.query(Solve.team_id, Solve.host, Flag.platform, Flag.perm)
        .join(Flag, Flag.id == Solve.flag_id)
        .all()
    )

    # Group solves by (team_id, host, platform) and track permission levels
    # Key: (team_id, host, platform) -> set of perms ('user', 'root')
    solve_perms = {}
    for solve in solves:
        key = (solve.team_id, solve.host, solve.platform.value if hasattr(solve.platform, 'value') else solve.platform)
        if key not in solve_perms:
            solve_perms[key] = set()
        perm_value = solve.perm.value if hasattr(solve.perm, 'value') else solve.perm
        solve_perms[key].add(perm_value)

    # Calculate scores
    # If both user and root: count as root (1 point)
    # If only root: 1 point
    # If only user: 0.5 points
    for (team_id, host, platform), perms in solve_perms.items():
        team_name = team_id_to_name.get(team_id)
        if not team_name:
            continue

        if "root" in perms:
            score = 1.0
        elif "user" in perms:
            score = 0.5
        else:
            score = 0.0

        # Add to appropriate platform score
        if platform == "win":
            totals[team_name][1] += score
        elif platform == "nix":
            totals[team_name][2] += score

    data = []
    for team in totals.values():
        data.append({"team": team[0], "win_score": team[1], "nix_score": team[2], "total_score": team[1] + team[2]})

    return jsonify(data=data)
