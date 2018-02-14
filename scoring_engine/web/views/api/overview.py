import pickle
import redis
import json
import random

from collections import OrderedDict

from flask import jsonify

from scoring_engine.db import session
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.config import config

from . import mod


@mod.route('/api/overview/get_round_data')
def overview_get_round_data():
    round_obj = session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        round_start = round_obj.local_round_start
        number = round_obj.number
    else:
        round_start = ""
        number = 0
    data = {'round_start': round_start, 'number': number}
    return jsonify(data)


@mod.route('/api/overview/data')
def overview_data():
    team_data = OrderedDict()
    teams = session.query(Team).filter(Team.color == 'Blue').order_by(Team.id).all()
    random.shuffle(teams)
    for team in teams:
        service_data = {}
        for service in team.services:
            service_data[service.name] = {
                'passing': service.last_check_result(),
                'host': service.host,
                'port': service.port,
            }
        team_data[team.name] = service_data
    return json.dumps(team_data)


def get_service_columns():
    blue_team = session.query(Team).filter(Team.color == 'Blue').first()
    columns = []
    columns.append({'title': 'Team Name', 'data': 'Team Name'})
    columns.append({'title': 'Current Score', 'data': 'Current Score'})
    for service in blue_team.services:
        columns.append({'title': service.name, 'data': service.name})
    return columns


@mod.route('/api/overview/get_columns')
def overview_get_columns():
    return jsonify(columns=get_service_columns())


@mod.route('/api/overview/get_data')
def overview_get_data():
    r = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=0)
    data = r.get('get_data')
    if data:
        return jsonify(pickle.loads(data))
    else:
        # TODO add updating, but in a way that does murder the database
        return jsonify({})
