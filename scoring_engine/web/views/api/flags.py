from datetime import datetime, timedelta, timezone

from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import case, func
from sqlalchemy.sql.expression import and_, or_

from scoring_engine.cache import agent_cache, cache
from scoring_engine.db import db
from scoring_engine.models.flag import Flag, Perm, Platform, Solve
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team

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
        db.session.query(Flag)
        .filter(and_(early > Flag.start_time, now < Flag.end_time, Flag.dummy == False))
        .order_by(Flag.start_time)
        .all()
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
    active_flags = (
        db.session.query(Flag)
        .filter(and_(now > Flag.start_time, now < Flag.end_time, Flag.dummy == False))
        .order_by(Flag.start_time)
        .all()
    )
    active_flag_ids = [flag.id for flag in active_flags]

    # Flag Solve Status
    all_hosts = (
        db.session.query(
            Service.name.label("service_name"),
            Service.port,
            Service.team_id,
            Service.host,
            Team.name.label("team_name"),
            func.coalesce(Solve.id, None).label("solve_id"),
            func.coalesce(Flag.id, None).label("flag_id"),
            func.coalesce(Flag.perm, None).label("flag_perm"),
            func.coalesce(Flag.platform, None).label("flag_platform"),
        )
        .select_from(Service)
        .filter(Service.check_name == "AgentCheck")
        .outerjoin(
            Solve,
            and_(Solve.host == Service.host, Solve.team_id == Service.team_id, Solve.flag_id.in_(active_flag_ids)),
        )
        .outerjoin(Flag, Flag.id == Solve.flag_id)
        .outerjoin(Team, Team.id == Service.team_id)
        .order_by(Service.name, Service.team_id)
        .all()
    )

    # Determine offline threshold: 2x agent checkin interval
    checkin_setting = Setting.get_setting("agent_checkin_interval_sec")
    checkin_interval = int(checkin_setting.value) if checkin_setting else 60
    offline_threshold = checkin_interval * 2
    now_ts = int(datetime.now(timezone.utc).timestamp())

    # Collect all unique hosts and build checkin timestamp map
    host_set = set()
    for item in all_hosts:
        host_set.add(item.host)

    # Batch query agent_cache for all hosts
    host_checkin = {}
    for host in host_set:
        cached = agent_cache.get(host)
        if cached and isinstance(cached, dict) and "timestamp" in cached:
            host_checkin[host] = cached["timestamp"]

    data = {}
    host_map = {}  # (team_name, service_name) -> host
    rows = []
    columns = ["Team"]

    for item in all_hosts:
        if item.service_name not in columns:
            columns.append(item.service_name)
        if not data.get(item.team_name):
            data[item.team_name] = {}
            host_map[item.team_name] = {}
        if not data[item.team_name].get(item.service_name):
            # [user_solve, root_solve, offline]
            data[item.team_name][item.service_name] = [0, 0, 0]
            host_map[item.team_name][item.service_name] = item.host
        if item.solve_id:
            if item.flag_perm.value == "user":
                data[item.team_name][item.service_name][0] = 1
            else:
                data[item.team_name][item.service_name][1] = 1

    # Mark offline hosts (only when no solve — solves take precedence)
    for team_name, services in data.items():
        for svc_name, solve_data in services.items():
            if solve_data[0] == 0 and solve_data[1] == 0:
                host = host_map.get(team_name, {}).get(svc_name)
                if host:
                    last_ts = host_checkin.get(host)
                    if last_ts is None or (now_ts - last_ts) > offline_threshold:
                        solve_data[2] = 1

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

    totals = {}
    blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    for blue_team in blue_teams:
        totals[blue_team.name] = [blue_team.name, 0, 0]

    # Subquery 1: Determine permission level per (team, platform, host, start_time).
    # If any root perm exists in the group → "root", otherwise → "user".
    perm_levels = (
        db.session.query(
            Solve.team_id,
            Flag.platform,
            Solve.host,
            case(
                (func.max(case((Flag.perm == Perm.root, 1), else_=0)) == 1, "root"),
                else_="user",
            ).label("level"),
        )
        .join(Flag, Flag.id == Solve.flag_id)
        .group_by(Solve.team_id, Flag.platform, Solve.host, Flag.start_time)
        .subquery()
    )

    # Subquery 2: Score each (team, platform, level) group.
    # COUNT(*) counts distinct (host, start_time) combinations per level.
    # user → 0.5 per combo, root → 1.0 per combo.
    scores = (
        db.session.query(
            perm_levels.c.team_id,
            perm_levels.c.platform,
            case(
                (perm_levels.c.level == "user", 0.5 * func.count()),
                else_=1.0 * func.count(),
            ).label("red_amt"),
        )
        .group_by(perm_levels.c.team_id, perm_levels.c.platform, perm_levels.c.level)
        .subquery()
    )

    # Final: Sum scores per (team, platform) and join to team names.
    results = (
        db.session.query(
            Team.name.label("BlueTeam"),
            scores.c.platform,
            func.sum(scores.c.red_amt).label("RedScore"),
        )
        .join(Team, scores.c.team_id == Team.id)
        .group_by(scores.c.team_id, scores.c.platform)
        .order_by(func.sum(scores.c.red_amt))
        .all()
    )

    for row in results:
        team_name = row[0]
        platform = row[1]
        score = float(row[2])
        if team_name not in totals:
            continue
        if platform in (Platform.windows, "windows", "win"):
            totals[team_name][1] = score
        elif platform in (Platform.nix, "nix"):
            totals[team_name][2] = score

    data = []
    for team in totals.values():
        data.append({"team": team[0], "win_score": team[1], "nix_score": team[2], "total_score": team[1] + team[2]})

    return jsonify(data=data)
