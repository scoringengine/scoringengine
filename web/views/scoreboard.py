from flask import Blueprint, render_template

mod = Blueprint('scoreboard', __name__)


@mod.route('/scoreboard')
def home():
    team1 = [0, 100, 200, 300, 400, 500]
    team2 = [0, 200, 300, 400, 400, 600]
    team3 = [0, 300, 300, 300, 300, 400]

    teamData = {
        "1": {
            "label": "Team 1",
            "data": team1
        },
        "2": {
            "label": "Team 2",
            "data": team2
        },
        "3": {
            "label": "Team 3",
            "data": team3
        }
    }

    return render_template('scoreboard.html', teamData=teamData)
