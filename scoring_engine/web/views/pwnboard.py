from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


mod = Blueprint('pwnboard', __name__)


@mod.route('/pwnboard')
@login_required
def home():
    if not current_user.is_red_team:
        return redirect(url_for('auth.unauthorized'))
    blue_teams = Team.get_all_blue_teams()
    red_users = User.get_all_red_users()
    return render_template('pwnboard.html', blue_teams=blue_teams, red_users=red_users)


@mod.route('/pwnboard/service/<id>')
@login_required
def pwnboard_service(id):
    if not current_user.is_red_team:
        return redirect(url_for('auth.unauthorized'))
    blue_teams = Team.get_all_blue_teams()
    return render_template('pwnboardservice.html', blue_teams=blue_teams, id=id)
