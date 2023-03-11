from collections import defaultdict
from flask import jsonify
from itertools import accumulate
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import mod


@mod.route("/api/scoreboard/get_bar_data")
@cache.memoize()
def scoreboard_get_bar_data():
    current_scores = dict(
        session.query(Service.team_id, func.sum(Service.points))
        .join(Check)
        .filter(Check.result.is_(True))
        .group_by(Service.team_id)
        .all()
    )

    inject_scores = dict(
        session.query(Inject.team_id, func.sum(Inject.score))
        .filter(Inject.status == "Graded")
        .group_by(Inject.team_id)
        .all()
    )

    team_data = {}
    team_labels = []
    team_scores = []
    team_inject_scores = []
    blue_teams = (
        session.query(Team).filter(Team.color == "Blue").order_by(Team.id).all()
    )
    for blue_team in blue_teams:
        team_labels.append(blue_team.name)
        team_scores.append(str(current_scores.get(blue_team.id, 0)))
        team_inject_scores.append(str(inject_scores.get(blue_team.id, 0)))

    team_data["labels"] = team_labels
    team_data["service_scores"] = team_scores
    team_data["inject_scores"] = team_inject_scores
    return jsonify(team_data)


@mod.route("/api/scoreboard/get_line_data")
@cache.memoize()
def scoreboard_get_line_data():
    last_round = Round.get_last_round_num()

    team_data = {
        "team": [],
        "rounds": [f"Round {round}" for round in range(last_round + 1)],
    }

    blue_teams = (
        session.query(Team.id, Team.name, Team.rgb_color)
        .filter(Team.color == "Blue")
        .order_by(Team.id)
        .all()
    )

    """
    [(3, 1, Decimal('4500')),
    (3, 2, Decimal('4500')),
    (3, 3, Decimal('4400'))]
    """
    # Team ID, Round ID, Round Score
    # TODO - Might be able to ignore ordering by team_id since we're using a dict
    round_scores = (
        session.query(
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

    scores_dict = defaultdict(lambda: defaultdict(list))
    for team_id, round_id, round_score in round_scores:
        # Loop through our results and update the appropriate team's list
        scores_dict[team_id][round_id] = round_score

    for team_id, team_name, rgb_color in blue_teams:
        team_data["team"].append(
            {
                "name": team_name,
                "scores": list(accumulate(scores_dict[team_id].values(), initial=0)),
                "color": rgb_color,
            }
        )

    return jsonify(team_data)
