from flask import request, jsonify
from flask_login import current_user, login_required

import html

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.cache_helper import update_overview_data, update_services_navbar, update_service_data
from scoring_engine.models.account import Account
from scoring_engine.models.service import Service

from . import mod


@mod.route('/api/service/<id>/checks')
@login_required
@cache.memoize()
def service_get_checks(id):
    service = session.query(Service).get(id)
    if service is None or not current_user.team == service.team:
        return jsonify({'status': 'Unauthorized'}), 403
    data = []
    for check in service.checks_reversed:
        data.append({
            'round': check.round.number,
            'result': check.result,
            'timestamp': check.local_completed_timestamp,
            'reason': check.reason,
            'output': check.output,
        })
    return jsonify(data=data)


@mod.route('/api/service/update_account', methods=['POST'])
@login_required
def update_service_account_info():
    if current_user.is_white_team or current_user.is_blue_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            account = session.query(Account).get(int(request.form['pk']))
            if current_user.team == account.service.team or current_user.is_white_team:
                if account:
                    if request.form['name'] == 'username':
                        account.username = html.escape(request.form['value'])
                    elif request.form['name'] == 'password':
                        account.password = html.escape(request.form['value'])
                    session.add(account)
                    session.commit()
                    return jsonify({'status': 'Updated Account Information'})
                return jsonify({'error': 'Incorrect permissions'})
            return jsonify({'error': 'Incorrect permissions'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/service/update_host', methods=['POST'])
@login_required
def update_host():
    if current_user.is_blue_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if service.team == current_user.team and request.form['name'] == 'host':
                    service.host = html.escape(request.form['value'])
                    session.add(service)
                    session.commit()
                    update_overview_data()
                    update_services_data(service.team.id)
                    update_service_data(service.id)
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})
