from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
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

    return render_template('index.html', teamData=teamData)

app.run(host="127.0.0.1", debug=True)