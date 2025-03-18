from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
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
    if not current_user.is_red_team and not current_user.is_white_team:
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
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    active_flags = session.query(Flag).filter(and_(early > Flag.start_time, now < Flag.end_time, Flag.dummy == False)).order_by(Flag.start_time).all()
    active_flag_ids = [flag.id for flag in active_flags]

    # Flag Solve Status
    all_hosts = session.query(Service.name.label("service_name"), Service.port, Service.team_id, Service.host, Team.name.label("team_name"), func.coalesce(Solve.id, None).label("solve_id"), func.coalesce(Flag.id, None).label("flag_id"), func.coalesce(Flag.perm, None).label("flag_perm"), func.coalesce(Flag.platform, None).label("flag_platform")).select_from(Service).filter(Service.check_name == "AgentCheck").outerjoin(Solve, and_(Solve.host == Service.host, Solve.team_id == Service.team_id)).filter(or_(Solve.flag_id.in_(active_flag_ids), Solve.host.is_(None))).outerjoin(Flag, Flag.id == Solve.flag_id).join(Team, Team.id == Service.team_id).order_by(Service.name, Service.team_id).all()

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
            if (item.flag_platform.value == "win" and item.port == 0) or (item.flag_platform.value == "nix" and item.port == 1): # windows flags have port 0, nix have port 1
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
