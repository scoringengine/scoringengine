from flask import Blueprint, render_template
from scoring_engine.models.team import Team

mod = Blueprint('scoreboard', __name__)


@mod.route('/scoreboard')
def home():
    results = Team.get_all_rounds_results()
    team_data = {}
    # We start at one because that's how javascript expects the team_data
    current_index = 1
    for name in sorted(results['scores'].keys()):
        scores = results['scores'][name]
        rgb_color = results['rgb_colors'][name]
        team_data[current_index] = {
            "label": name,
            "data": scores,
            "color": rgb_color
        }
        current_index += 1

    team_labels = []
    team_scores = []
    scores_colors = []
    for blue_team in Team.get_all_blue_teams():
        team_labels.append(blue_team.name)
        team_scores.append(blue_team.current_score)
        scores_colors.append(blue_team.rgb_color)

    return render_template('scoreboard.html', round_labels=results['rounds'], team_data=team_data, team_labels=team_labels, team_scores=team_scores, scores_colors=scores_colors)


def generateRBGA():
    import random
    return "rgba(%s, %s, %s, 1)" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
