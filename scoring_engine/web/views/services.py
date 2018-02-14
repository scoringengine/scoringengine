from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user
from scoring_engine.models.service import Service
from scoring_engine.db import session


mod = Blueprint('services', __name__)


@mod.route('/services')
@login_required
def home():
    if not current_user.is_blue_team:
        return redirect(url_for('auth.unauthorized'))
    return render_template('services.html', team_name=current_user.team.name, team_id=current_user.team.id)


@mod.route('/service/<id>')
@login_required
def service(id):
    service = session.query(Service).get(id)
    if service is None or not current_user.team == service.team:
        return redirect(url_for('auth.unauthorized'))
    return render_template('service.html', id=id, service=service)
