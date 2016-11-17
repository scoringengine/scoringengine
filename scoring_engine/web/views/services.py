from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user
from scoring_engine.models.service import Service

mod = Blueprint('services', __name__)


@mod.route('/services')
@login_required
def home():
    current_team = current_user.team
    if not current_user.is_blue_team:
        return redirect(url_for('auth.unauthorized'))
    return render_template('services.html', team=current_team)


@mod.route('/service/<id>')
@login_required
def service(id):
    service = Service.query.get(id)
    if service is None or not current_user.team == service.team:
        return redirect(url_for('auth.unauthorized'))
    return render_template('service.html', service=service)
