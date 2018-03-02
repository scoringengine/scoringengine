from flask import jsonify

from scoring_engine.cache import cache
from scoring_engine.models.team import Team

from . import mod


@mod.route('/api/scoreboard/get_bar_data')
@cache.memoize
def scoreboard_get_bar_data():
    team_data = {}
    team_labels = []
    team_scores = []
    scores_colors = []
    for blue_team in Team.get_all_blue_teams():
        team_labels.append(blue_team.name)
        team_scores.append(blue_team.current_score)
        scores_colors.append(blue_team.rgb_color)

    team_data['labels'] = team_labels
    team_data['scores'] = team_scores
    team_data['colors'] = scores_colors
    return jsonify(team_data)


@mod.route('/api/scoreboard/get_line_data')
@cache.memoize
def scoreboard_get_line_data():
    results = Team.get_all_rounds_results()
    team_data = {'team': {}, 'round': results['rounds']}
    # We start at one because that's how javascript expects the team_data
    current_index = 1
    for name in results['scores'].keys():
        scores = results['scores'][name]
        rgb_color = results['rgb_colors'][name]
        team_data['team'][current_index] = {
            "label": name,
            "data": scores,
            "color": rgb_color
        }
        current_index += 1
    return jsonify(team_data)
