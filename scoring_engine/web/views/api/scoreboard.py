from flask import jsonify
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
        session.query(Team).filter(Team.color == "Blue").order_by(Team.name).all()
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
    results = Team.get_all_rounds_results()
    team_data = {"team": [], "rounds": results["rounds"]}
    if "team_names" in results.keys():
        for team_name in results["team_names"]:
            # TODO - Add inject score
            scores = list(map(str, results["scores"][team_name]))
            rgb_color = results["rgb_colors"][team_name]
            team_data["team"].append(
                {"name": team_name, "scores": scores, "color": rgb_color}
            )
    return jsonify(team_data)
