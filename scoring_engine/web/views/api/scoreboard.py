import json
import random

from flask import jsonify

from scoring_engine.cache import cache
from scoring_engine.models.team import Team
from . import mod


@mod.route("/api/scoreboard/get_bar_data")
@cache.memoize()
def scoreboard_get_bar_data():
    team_data = {}
    team_labels = []
    team_scores = []
    inject_scores = []
    scores_colors = []
    for blue_team in Team.get_all_blue_teams():
        team_labels.append(blue_team.name)
        team_scores.append(str(blue_team.current_score))
        inject_scores.append(str(blue_team.current_inject_score))
        # scores_colors.append(blue_team.rgb_color)

    team_data["labels"] = team_labels
    team_data["service_scores"] = team_scores
    team_data["inject_scores"] = inject_scores
    # team_data["colors"] = scores_colors
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
