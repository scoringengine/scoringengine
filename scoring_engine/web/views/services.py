from flask import Blueprint, render_template, url_for, redirect, jsonify
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
    return render_template('service.html', id=id, service=service)


@mod.route('/api/service/get_checks/<id>')
@login_required
def get_checks(id):
    service = Service.query.get(id)
    if service is None or not current_user.team == service.team:
        return jsonify({'status': 'Unauthorized'}), 403
    data = []
    for check in service.checks_reversed:
        data.append({'round': check.round.number,
                     'result': check.result,
                     'timestamp': check.completed_timestamp,
                     'output': check.output})
    return jsonify(data=data)
