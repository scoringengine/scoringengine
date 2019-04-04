from datetime import datetime, timedelta
from dns import reversename, resolver
from dns.resolver import NXDOMAIN
from flask import jsonify, request
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.pwnboard import Pwnboard
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

from . import mod


def reverse_dns(ip):
    rev_name = reversename.from_address(ip)
    try:
        reversed_dns = str(resolver.query(rev_name, "PTR")[0])
    except NXDOMAIN:
        return False
    # Strip off trailing .
    return reversed_dns[:-1]


@mod.route('/api/pwnboard/data')
@cache.memoize(10)
@login_required
def api_pwnboard_data():
    pwnboard_data = []

    # Get unique list of services
    for service in session.query(Service.name).distinct():
        row_data = {'Service': service[0]}
        # TODO - Figure out why distinct returns a tuple
        for row in session.query(Service).join(Service.team).filter(Service.name == service[0]).order_by(Team.id).all():
            row_data[row.team.name] = {
                'id': row.id,
                'host': row.host,
            }
            # TODO - Figure out how to do this without a million queries
            pwned = session.query(Pwnboard).filter(Pwnboard.service_id == row.id).order_by(Pwnboard.timestamp.desc()).first()
            # TODO - There has to be a better way to do this
            if pwned:
                row_data[row.team.name]['agent'] = pwned.agent
                row_data[row.team.name]['user'] = pwned.user.username
                row_data[row.team.name]['timestamp'] = pwned.timestamp
            else:
                row_data[row.team.name]['agent'] = None
                row_data[row.team.name]['user'] = None
                row_data[row.team.name]['timestamp'] = None
        pwnboard_data.append(row_data)
    return jsonify(data=pwnboard_data)


@mod.route('/api/pwnboard/data/<user>')
@cache.memoize(10)
@login_required
def api_pwnboard_data_user(user):
    pwnboard_data = []

    # Get unique list of services
    for service in session.query(Service.name).distinct():
        row_data = {'Service': service[0]}
        # TODO - Figure out why distinct returns a tuple
        for row in session.query(Service).join(Service.team).filter(Service.name == service[0]).order_by(Team.id).all():
            row_data[row.team.name] = {
                'id': row.id,
                'host': row.host,
            }
            # TODO - Figure out how to do this without a million queries
            pwned = session.query(Pwnboard).join(User).filter(Pwnboard.service_id == row.id).filter(User.username == user).order_by(Pwnboard.timestamp.desc()).first()
            # TODO - There has to be a better way to do this
            if pwned:
                row_data[row.team.name]['agent'] = pwned.agent
                row_data[row.team.name]['user'] = pwned.user.username
                row_data[row.team.name]['timestamp'] = pwned.timestamp
            else:
                row_data[row.team.name]['agent'] = None
                row_data[row.team.name]['user'] = None
                row_data[row.team.name]['timestamp'] = None
        pwnboard_data.append(row_data)
    return jsonify(data=pwnboard_data)


@mod.route('/api/pwnboard/service/<id>')
@login_required
def api_pwnboard_id(id):
    results = session.query(Pwnboard).filter(Pwnboard.service_id == id).order_by(Pwnboard.timestamp.desc()).all()
    if results:
        data = []
        for result in results:
            data.append({
                'agent': result.agent,
                'user': result.user.username,
                'timestamp': result.timestamp,
            })
        return jsonify(data=data)
    return jsonify(data=[])


@mod.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.get_json()
    source_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if data:
        # Error if token does not exist in DB
        if 'token' not in data:
            return jsonify({'status': 'error', 'message': 'Token Required.'}), 400
        # Token provided
        else:
            user = session.query(User).join(Team).filter(User.token == data['token']).filter(Team.color == 'Red').first()
            # Token exists in user DB
            if user:
                try:
                    host = reverse_dns(source_address)
                    service = session.query(Service).filter_by(host=host).first()
                    if not service:
                        return jsonify({'status': 'error', 'message': 'Service not found for {}'.format(host)}), 400

                    # User has already checked in this service this hour
                    now = datetime.utcnow()
                    # Get number of check-ins for this user this hour
                    res = session.query(Pwnboard).filter(Pwnboard.user == user)\
                        .filter(Pwnboard.timestamp > now.replace(minute=0, second=0, microsecond=0))\
                        .filter(Pwnboard.timestamp < (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)))\
                        .count()

                    # Add Pwnboard check-in
                    pwned = Pwnboard(user=user,
                                     service=service,
                                     source_address=source_address,
                                     agent=data.get('agent', None))
                    session.add(pwned)
                    session.commit()
                except SQLAlchemyError:
                    session.rollback()
                    return jsonify({'status': 'error', 'message': 'Error saving to database.'}), 400
                if res > 0:
                    return jsonify({'status': 'success',
                                    'message': 'You have already checked in this service this hour.'}), 200
                else:
                    return jsonify({'status': 'success', 'message': 'Check-in successful.'}), 200
            # Invalid Token
            else:
                return jsonify({'status': 'error', 'message': 'Invalid Token.'}), 400
    # Invalid JSON
    else:
        return jsonify({'status': 'error', 'message': 'Valid JSON not received. '
                                                      'Please you have -H "Content-Type: application/json"'}), 400
