import html
from collections import defaultdict
from functools import wraps

import pytz
from flask import jsonify, request
from flask_login import current_user, login_required
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


from scoring_engine.cache_helper import update_overview_data, update_service_data, update_services_data
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.sla import get_sla_config, apply_dynamic_scoring_to_round, calculate_team_total_penalties
from scoring_engine.web.views.api.overview import calculate_ranks

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
            Round.number.label("round_id"),
            Round.round_start,
            Round.round_end,
            Service.name.label("service_name"),
            func.sum(case((Check.result.is_(True), 1), else_=0)).label("num_successful_checks"),
            func.sum(case((Check.result.is_(False), 1), else_=0)).label("num_unsuccessful_checks"),
        )
        .join(Check, Round.id == Check.round_id)
        .join(Service, Check.service_id == Service.id)
        .filter(Round.number <= last_round)
    )

    if team_id is not None:
        query = query.filter(Service.team_id == team_id)

    return (
        query.group_by(Round.number, Round.round_start, Round.round_end, Service.name)
        .order_by(Round.number.desc(), Service.name)
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
                "start_time": _ensure_utc_aware(round_start).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
                "end_time": _ensure_utc_aware(round_end).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
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
    stats = sorted(rounds.values(), key=lambda r: r["round_id"], reverse=True)

    return {"data": stats, "summary": dict(summary)}


@mod.route("/api/stats")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_stats():
    team = db.session.get(Team, current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_blue_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    if current_user.is_blue_team:
        rows = _build_stats_query(team_id=team.id)
        return jsonify(_build_response(rows))

    if current_user.is_white_team:
        rows = _build_stats_query(team_id=None)
        return jsonify(_build_response(rows))

    return {"status": "Unauthorized"}, 403


@mod.route("/api/stats/scoring_overview")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_stats_scoring_overview():
    """Scoring overview tables with ordinal rankings. White team only."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    blue_team_ids = [t.id for t in blue_teams]
    blue_teams_dict = {t.id: t for t in blue_teams}

    sla_config = get_sla_config()

    # --- Service Scores ---
    if sla_config.dynamic_enabled:
        from collections import defaultdict

        round_scores = (
            db.session.query(Service.team_id, Check.round_id, func.sum(Service.points).label("round_score"))
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id, Check.round_id)
            .all()
        )
        rounds_map = {r.id: r.number for r in db.session.query(Round.id, Round.number).all()}
        team_scores = defaultdict(int)
        for team_id, round_id, round_score in round_scores:
            round_number = rounds_map.get(round_id, 0)
            team_scores[team_id] += apply_dynamic_scoring_to_round(round_number, round_score, sla_config)
        team_scores = dict(team_scores)
    else:
        from sqlalchemy import desc

        team_scores = dict(
            db.session.query(Service.team_id, func.sum(Service.points).label("score"))
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .all()
        )

    # Apply SLA penalties
    adjusted_scores = {}
    for tid in blue_team_ids:
        base = team_scores.get(tid, 0)
        if sla_config.sla_enabled:
            penalty = calculate_team_total_penalties(blue_teams_dict[tid], sla_config)
            adjusted_scores[tid] = max(0, base - penalty) if not sla_config.allow_negative else base - penalty
        else:
            adjusted_scores[tid] = base

    service_ranks = calculate_ranks(adjusted_scores)

    service_table = []
    for t in blue_teams:
        service_table.append({
            "team": t.name,
            "score": adjusted_scores.get(t.id, 0),
            "rank": service_ranks.get(t.id, 0),
        })

    # --- Inject Scores by Category ---
    from scoring_engine.models.inject import InjectRubricScore

    inject_rows = (
        db.session.query(
            Inject.team_id,
            Template.category,
            func.coalesce(func.sum(InjectRubricScore.score), 0).label("total_score"),
        )
        .join(Template, Inject.template_id == Template.id)
        .outerjoin(InjectRubricScore, InjectRubricScore.inject_id == Inject.id)
        .filter(Inject.team_id.in_(blue_team_ids))
        .group_by(Inject.team_id, Template.category)
        .all()
    )

    # Build per-team category scores
    from collections import defaultdict

    cat_scores = defaultdict(lambda: defaultdict(int))
    for team_id, category, score in inject_rows:
        cat_scores[team_id][category or "Uncategorized"] = int(score)

    categories = ["Business", "Technical", "Incident Response"]

    # Calculate ranks per category
    cat_rank_dicts = {}
    for cat in categories:
        cat_rank_dicts[cat] = calculate_ranks({tid: cat_scores[tid].get(cat, 0) for tid in blue_team_ids})

    # Business + Technical summary
    bt_scores = {tid: cat_scores[tid].get("Business", 0) + cat_scores[tid].get("Technical", 0) for tid in blue_team_ids}
    bt_ranks = calculate_ranks(bt_scores)

    # Total inject scores
    total_inject = {tid: sum(cat_scores[tid].values()) for tid in blue_team_ids}
    total_inject_ranks = calculate_ranks(total_inject)

    inject_table = []
    for t in blue_teams:
        row = {"team": t.name}
        for cat in categories:
            row[f"score_{cat}"] = cat_scores[t.id].get(cat, 0)
            row[f"rank_{cat}"] = cat_rank_dicts[cat].get(t.id, 0)
        row["score_bt"] = bt_scores.get(t.id, 0)
        row["rank_bt"] = bt_ranks.get(t.id, 0)
        row["score_total"] = total_inject.get(t.id, 0)
        row["rank_total"] = total_inject_ranks.get(t.id, 0)
        inject_table.append(row)

    return jsonify({
        "service_table": service_table,
        "inject_table": inject_table,
        "categories": categories,
    })
