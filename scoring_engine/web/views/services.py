from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user

mod = Blueprint('services', __name__)


@mod.route('/services')
@login_required
def home():
    current_team = current_user.team
    if not current_user.is_blue_team:
        flash('Only blue teams can access services', 'error')
        return render_template('overview.html')
    return render_template('services.html', team=current_team)


@mod.route('/service/<id>')
@login_required
def service(id):
    return render_template('service.html', service=id)
