from collections import defaultdict

from flask import jsonify
from sqlalchemy import desc
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.sla import (apply_dynamic_scoring_to_round,
                                calculate_team_total_penalties, get_sla_config)

from . import mod


def calculate_ranks(score_dict):
    """
    Calculate ranks for a dict of {id: score} with tie handling.
    Returns dict of {id: rank} where ties get the same rank.
    """
    if not score_dict:
        return {}
    sorted_items = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    ranks = {}
    current_rank = 1
    prev_score = None
    for i, (item_id, score) in enumerate(sorted_items):
        if prev_score is not None and score < prev_score:
            current_rank = i + 1
        ranks[item_id] = current_rank
        prev_score = score
    return ranks


def get_table_columns():
    blue_teams = Team.get_all_blue_teams()
    columns = []
    columns.append({"title": "", "data": ""})
    for team in blue_teams:
        columns.append({"title": team.name, "data": team.name})
    return columns


@mod.route("/api/overview/get_round_data")
@cache.memoize()
def overview_get_round_data():
    round_obj = db.session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        round_start = round_obj.local_round_start
        number = round_obj.number
    else:
        round_start = ""
        number = 0
    data = {"round_start": round_start, "number": number}
    return jsonify(data)


@mod.route("/api/overview/data")
@cache.memoize()
def overview_data():
    data = defaultdict(lambda: defaultdict(dict))

    round_obj = db.session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        checks = (
            db.session.query(Check.service_id, Check.result)
            .join(Round)
            .filter(Round.number == round_obj.number)
            .subquery()
        )
        res = (
            db.session.query(
                Team.name, Service.name, Service.host, Service.port, checks.c.result
            )
            .join(Team)
            .filter(checks.c.service_id == Service.id)
            .all()
        )

        for r in res:
            data[r[0]][r[1]] = {
                "host": r[2],
                "port": r[3],
                "passing": r[4],
            }

    return jsonify(data)


@mod.route("/api/overview/get_columns")
@cache.memoize()
def overview_get_columns():
    return jsonify(columns=get_table_columns())


@mod.route("/api/overview/get_data")
@cache.memoize()
def overview_get_data():
    # columns = get_table_columns()
    data = []
    blue_teams = (
        db.session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    )
    blue_team_ids = [team.id for team in blue_teams]
    blue_teams_dict = {team.id: team for team in blue_teams}
    last_round = Round.get_last_round_num()

    # Get SLA configuration
    sla_config = get_sla_config()

    current_scores = ["Current Score"]
    current_places = ["Current Place"]
    service_ratios = ["Up/Down Ratio"]
    sla_penalties_row = ["SLA Penalties"]

    num_up_services = dict(
        db.session.query(
            Service.team_id,
            func.count(Service.team_id),
        )
        .join(Check)
        .join(Round)
        .filter(Check.result.is_(True))
        .filter(Round.number == last_round)
        .group_by(Service.team_id)
        .all()
    )

    num_down_services = dict(
        db.session.query(
            Service.team_id,
            func.count(Service.team_id),
        )
        .join(Check)
        .join(Round)
        .filter(Check.result.is_(False))
        .filter(Round.number == last_round)
        .group_by(Service.team_id)
        .all()
    )

    if len(blue_team_ids) > 0:
        # Calculate team scores with dynamic scoring multipliers
        if sla_config.dynamic_enabled:
            # Query scores per round for dynamic scoring
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
            rounds_map = {
                r.id: r.number for r in db.session.query(Round.id, Round.number).all()
            }

            # Calculate totals with multipliers
            team_scores = defaultdict(int)
            for team_id, round_id, round_score in round_scores:
                round_number = rounds_map.get(round_id, 0)
                adjusted_score = apply_dynamic_scoring_to_round(
                    round_number, round_score, sla_config
                )
                team_scores[team_id] += adjusted_score
            team_scores = dict(team_scores)
        else:
            # No dynamic scoring - use simple sum
            team_scores = dict(
                db.session.query(
                    Service.team_id, func.sum(Service.points).label("score")
                )
                .join(Check)
                .filter(Check.result.is_(True))
                .group_by(Service.team_id)
                .order_by(desc("score"))
                .all()
            )

        # Calculate adjusted scores with SLA penalties
        adjusted_scores_dict = {}
        penalties_dict = {}
        for blue_team_id in blue_team_ids:
            base_score = team_scores.get(blue_team_id, 0)
            if sla_config.sla_enabled:
                team = blue_teams_dict[blue_team_id]
                penalty = calculate_team_total_penalties(team, sla_config)
                penalties_dict[blue_team_id] = penalty
                if sla_config.allow_negative:
                    adjusted_scores_dict[blue_team_id] = base_score - penalty
                else:
                    adjusted_scores_dict[blue_team_id] = max(0, base_score - penalty)
            else:
                penalties_dict[blue_team_id] = 0
                adjusted_scores_dict[blue_team_id] = base_score

        # Use adjusted scores for ranking when SLA is enabled
        scores_for_ranking = (
            adjusted_scores_dict if sla_config.sla_enabled else team_scores
        )

        # Calculate ranks with tie handling
        ranks_dict = calculate_ranks(scores_for_ranking)

        for blue_team_id in blue_team_ids:
            # Show adjusted score when SLA is enabled, base score otherwise
            if sla_config.sla_enabled:
                current_scores.append(str(adjusted_scores_dict.get(blue_team_id, 0)))
            else:
                current_scores.append(str(team_scores.get(blue_team_id, 0)))
            current_places.append(str(ranks_dict.get(blue_team_id, 0)))
            service_ratios.append(
                '<span class="text-success">{0} <span class="glyphicon glyphicon-arrow-up"></span></span> / '
                '<span class="text-danger">{1} <span class="glyphicon glyphicon-arrow-down"></span></span>'.format(
                    num_up_services.get(blue_team_id, 0),
                    num_down_services.get(blue_team_id, 0),
                )
            )
            # Add penalty display (negative number if penalty exists)
            penalty = penalties_dict.get(blue_team_id, 0)
            if penalty > 0:
                sla_penalties_row.append(
                    '<span class="text-danger">-{}</span>'.format(penalty)
                )
            else:
                sla_penalties_row.append("0")

        data.append(current_scores)
        data.append(current_places)
        # Show SLA penalties row when SLA is enabled
        if sla_config.sla_enabled:
            data.append(sla_penalties_row)
        data.append(service_ratios)

        checks = (
            db.session.query(Service.name, Check.result)
            .join(Service)
            .join(Round)
            .filter(Round.number == last_round)
            .order_by(Service.name, Service.team_id)
            .all()
        )

        service_dict = defaultdict(list)

        # Loop through each check and create a default dictionary
        """
        {'SERVICE': [True,
              True,
              False,
              False,
              False,
              False,
              False,
              True,
              False,
              True]
        """
        for service, status in checks:
            service_dict[service].append(status)

        # Loop through dictionary to create datatables formatted list
        for k, v in service_dict.items():
            data.append(
                [k] + v
            )  # ['SERVICE', True, False, False, False, False, False, False, True, False, False]
        return jsonify(data=data)
    else:
        return "{}"
