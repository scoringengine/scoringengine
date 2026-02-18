import html
from collections import defaultdict
from functools import wraps

import pytz
from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import desc
from sqlalchemy.sql import case, func

from scoring_engine.cache import cache


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return pytz.utc.localize(dt)
    # Already aware - convert to UTC
    return dt.astimezone(pytz.utc)
from scoring_engine.cache_helper import (update_overview_data,
                                         update_service_data,
                                         update_services_data)
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team

from . import make_cache_key, mod


def _build_stats_query(team_id=None):
    """Build the stats query with service-type breakdown.

    Parameters
    ----------
    team_id : int, optional
        If provided, filter checks to only this team's services.
        If None, include all teams (white team view).

    Returns
    -------
    list
        Query results with columns: round_id, round_start, round_end,
        service_name, num_successful_checks, num_unsuccessful_checks.
    """
    last_round = Round.get_last_round_num()
    query = (
        db.session.query(
            Round.id.label("round_id"),
            Round.round_start,
            Round.round_end,
            Service.name.label("service_name"),
            func.sum(case((Check.result == True, 1), else_=0)).label(
                "num_successful_checks"
            ),
            func.sum(case((Check.result == False, 1), else_=0)).label(
                "num_unsuccessful_checks"
            ),
        )
        .outerjoin(Check, Round.id == Check.round_id)
        .join(Service, Check.service_id == Service.id)
        .filter(Round.id <= last_round)
    )

    if team_id is not None:
        query = query.filter(Service.team_id == team_id)

    return (
        query.group_by(
            Round.id, Round.round_start, Round.round_end, Service.name
        )
        .order_by(Round.id.desc(), Service.name)
        .all()
    )


def _build_response(rows):
    """Aggregate query rows into per-round stats with service breakdown
    and all-time summary.

    Parameters
    ----------
    rows : list
        Query results from _build_stats_query.

    Returns
    -------
    dict
        Response with 'data' (per-round) and 'summary' (all-time) keys.
    """
    tz = pytz.timezone(config.timezone)

    # Group rows by round
    rounds = {}
    summary = defaultdict(lambda: {"up": 0, "down": 0, "total": 0})

    for row in rows:
        round_id = row[0]
        round_start = row[1]
        round_end = row[2]
        service_name = row[3]
        up = row[4]
        down = row[5]

        if round_id not in rounds:
            rounds[round_id] = {
                "round_id": round_id,
                "start_time": _ensure_utc_aware(round_start)
                .astimezone(tz)
                .strftime("%Y-%m-%d %H:%M:%S %Z"),
                "end_time": _ensure_utc_aware(round_end)
                .astimezone(tz)
                .strftime("%Y-%m-%d %H:%M:%S %Z"),
                "total_seconds": (round_end - round_start).seconds,
                "num_up_services": 0,
                "num_down_services": 0,
                "service_breakdown": {},
            }

        entry = rounds[round_id]
        entry["num_up_services"] += up
        entry["num_down_services"] += down
        entry["service_breakdown"][service_name] = {
            "up": up,
            "down": down,
        }

        # Accumulate all-time summary
        summary[service_name]["up"] += up
        summary[service_name]["down"] += down
        summary[service_name]["total"] += up + down

    # Sort by round_id descending
    stats = sorted(
        rounds.values(), key=lambda r: r["round_id"], reverse=True
    )

    return {"data": stats, "summary": dict(summary)}


@mod.route("/api/stats")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_stats():
    team = db.session.get(Team, current_user.team.id)
    if (
        team is None
        or not current_user.team == team
        or not (current_user.is_blue_team or current_user.is_white_team)
    ):
        return jsonify({"status": "Unauthorized"}), 403

    if current_user.is_blue_team:
        rows = _build_stats_query(team_id=team.id)
        return jsonify(_build_response(rows))

    if current_user.is_white_team:
        rows = _build_stats_query(team_id=None)
        return jsonify(_build_response(rows))

    return {"status": "Unauthorized"}, 403
