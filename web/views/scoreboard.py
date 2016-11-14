from flask import Blueprint, render_template

scoreboard_view = Blueprint('scoreboard', __name__)


@scoreboard_view.route('/scoreboard')
def home():
    return render_template('scoreboard.html')
