from collections import defaultdict
from itertools import accumulate

from flask import jsonify
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.flag import Flag, Perm, Platform, Solve
from scoring_engine.models.inject import Inject
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.sla import apply_dynamic_scoring_to_round, calculate_team_total_penalties, get_sla_config

from . import mod


def calculate_team_scores_with_dynamic_scoring(sla_config):
    """
    Calculate team scores with dynamic scoring multipliers applied per-round.

    Returns dict mapping team_id to total score with multipliers applied.
    """
    if not sla_config.dynamic_enabled:
        # No dynamic scoring - use simple sum
        return dict(
            db.session.query(Service.team_id, func.sum(Service.points))
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .all()
        )

    # Query scores grouped by team and round
    round_scores = (
        db.session.query(
            Service.team_id,
            Check.round_id,
            func.sum(Service.points).label("round_score"),
        )
        .join(Check)
        .filter(Check.result.is_(True))
        .group_by(Service.team_id, Check.round_id)
        .all()
    )

    # Get round numbers for each round_id
    rounds = {r.id: r.number for r in db.session.query(Round.id, Round.number).all()}

    # Calculate total with multipliers
    team_scores = defaultdict(int)
    for team_id, round_id, round_score in round_scores:
        round_number = rounds.get(round_id, 0)
        adjusted_score = apply_dynamic_scoring_to_round(round_number, round_score, sla_config)
        team_scores[team_id] += adjusted_score

    return dict(team_scores)


@mod.route("/api/scoreboard/get_bar_data")
@cache.memoize()
def scoreboard_get_bar_data():
    # Get SLA configuration first (needed for dynamic scoring)
    sla_config = get_sla_config()

    current_scores = calculate_team_scores_with_dynamic_scoring(sla_config)

    inject_scores = dict(
        db.session.query(Inject.team_id, func.sum(Inject.score))
        .filter(Inject.status == "Graded")
        .group_by(Inject.team_id)
        .all()
    )

    team_data = {}
    team_labels = []
    team_scores = []
    team_inject_scores = []
    team_sla_penalties = []
    team_adjusted_scores = []

    blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    for blue_team in blue_teams:
        team_labels.append(blue_team.name)
        service_score = current_scores.get(blue_team.id, 0)
        inject_score = inject_scores.get(blue_team.id, 0)
        team_scores.append(str(service_score))
        team_inject_scores.append(str(inject_score))

        # Calculate SLA penalties if enabled
        # Total base score includes both service and inject scores
        total_base_score = service_score + inject_score
        if sla_config.sla_enabled:
            penalty = calculate_team_total_penalties(blue_team, sla_config)
            team_sla_penalties.append(str(penalty))
            if sla_config.allow_negative:
                adjusted = total_base_score - penalty
            else:
                adjusted = max(0, total_base_score - penalty)
            team_adjusted_scores.append(str(adjusted))
        else:
            team_sla_penalties.append("0")
            team_adjusted_scores.append(str(total_base_score))

    team_data["labels"] = team_labels
    team_data["service_scores"] = team_scores
    team_data["inject_scores"] = team_inject_scores
    team_data["sla_penalties"] = team_sla_penalties
    team_data["adjusted_scores"] = team_adjusted_scores
    team_data["sla_enabled"] = sla_config.sla_enabled
    return jsonify(team_data)


@mod.route("/api/scoreboard/get_line_data")
@cache.memoize()
def scoreboard_get_line_data():
    last_round = Round.get_last_round_num()
    sla_config = get_sla_config()

    team_data = {
        "team": [],
        "rounds": [f"Round {round}" for round in range(last_round + 1)],
    }

    blue_teams = (
        db.session.query(Team.id, Team.name, Team.rgb_color).filter(Team.color == "Blue").order_by(Team.id).all()
    )

    """
    [(3, 1, Decimal('4500')),
    (3, 2, Decimal('4500')),
    (3, 3, Decimal('4400'))]
    """
    # Team ID, Round ID, Round Score
    # TODO - Might be able to ignore ordering by team_id since we're using a dict
    round_scores = (
        db.session.query(
            Service.team_id,
            Check.round_id,
            func.sum(Service.points),
        )
        .join(Check)
        .filter(Check.result.is_(True))
        .group_by(Service.team_id, Check.round_id)
        .order_by(Service.team_id, Check.round_id)
        .all()
    )

    # Get round numbers for dynamic scoring
    rounds_map = {r.id: r.number for r in db.session.query(Round.id, Round.number).all()}

    scores_dict = defaultdict(lambda: defaultdict(int))
    for team_id, round_id, round_score in round_scores:
        # Apply dynamic scoring multiplier if enabled
        round_number = rounds_map.get(round_id, 0)
        adjusted_score = apply_dynamic_scoring_to_round(round_number, round_score, sla_config)
        scores_dict[team_id][round_id] = adjusted_score

    for team_id, team_name, rgb_color in blue_teams:
        team_data["team"].append(
            {
                "name": team_name,
                "scores": list(accumulate(scores_dict[team_id].values(), initial=0)),
                "color": rgb_color,
            }
        )

    return jsonify(team_data)


@mod.route("/api/scoreboard/get_red_team_data")
@cache.memoize()
def scoreboard_get_red_team_data():
    """
    Get red team capture statistics for the scoreboard.

    Scoring:
    - Root capture = 1.0 point per platform
    - User capture = 0.5 points per platform

    Returns captures grouped by team with platform breakdown.
    """
    # Get all non-dummy flags and their solves
    solves = db.session.query(Solve).join(Flag).filter(Flag.dummy.is_(False)).all()

    # Get all blue teams
    blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()

    # Initialize team capture data
    team_captures = {}
    for team in blue_teams:
        team_captures[team.id] = {
            "team": team.name,
            "team_id": team.id,
            "nix_user": 0,
            "nix_root": 0,
            "nix_score": 0.0,
            "windows_user": 0,
            "windows_root": 0,
            "windows_score": 0.0,
            "total_captures": 0,
            "total_score": 0.0,
        }

    # Aggregate captures by team and platform
    for solve in solves:
        flag = solve.flag
        team_id = solve.team_id

        if team_id not in team_captures:
            continue

        # Determine score: root = 1.0, user = 0.5
        score = 1.0 if flag.perm == Perm.root else 0.5

        if flag.platform == Platform.nix:
            if flag.perm == Perm.root:
                team_captures[team_id]["nix_root"] += 1
            else:
                team_captures[team_id]["nix_user"] += 1
            team_captures[team_id]["nix_score"] += score
        elif flag.platform == Platform.windows:
            if flag.perm == Perm.root:
                team_captures[team_id]["windows_root"] += 1
            else:
                team_captures[team_id]["windows_user"] += 1
            team_captures[team_id]["windows_score"] += score

        team_captures[team_id]["total_captures"] += 1
        team_captures[team_id]["total_score"] += score

    # Calculate totals
    total_captures = sum(t["total_captures"] for t in team_captures.values())
    total_red_points = sum(t["total_score"] for t in team_captures.values())

    return jsonify(
        {
            "captures": list(team_captures.values()),
            "total_captures": total_captures,
            "total_red_points": total_red_points,
        }
    )
