from flask import Blueprint, render_template

mod = Blueprint('scoreboard', __name__)


@mod.route('/scoreboard')
def home():
    return render_template('scoreboard.html')
