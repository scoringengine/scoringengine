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
            "data": team1,
            "color": generateRBGA()
        },
        "2": {
            "label": "Team 2",
            "data": team2,
            "color": generateRBGA()
        },
        "3": {
            "label": "Team 3",
            "data": team3,
            "color": generateRBGA()
        }
    }

    return render_template('scoreboard.html', teamData=teamData)


def generateRBGA():
    import random
    return "rgba(%s, %s, %s, 1)" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
