import json
import random

from collections import OrderedDict

from flask import jsonify

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team

from . import mod


def get_service_columns():
    blue_team = session.query(Team).filter(Team.color == 'Blue').first()
    columns = []
    columns.append({'title': 'Team Name', 'data': 'Team Name'})
    columns.append({'title': 'Current Score', 'data': 'Current Score'})
    for service in blue_team.services:
        columns.append({'title': service.name, 'data': service.name})
    return columns


@mod.route('/api/overview/get_round_data')
@cache.memoize()
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
@cache.memoize()
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


@mod.route('/api/overview/get_columns')
@cache.memoize()
def overview_get_columns():
    return jsonify(columns=get_service_columns())


@mod.route('/api/overview/get_data')
@cache.memoize()
def overview_get_data():
    blue_teams = session.query(Team).filter(Team.color == 'Blue').all()
    columns = []
    columns.append('Team Name')
    columns.append('Current Score')
    if len(blue_teams) > 0:
        for service in blue_teams[0].services:
            columns.append(service.name)
        data = []
        for team in blue_teams:
            count = 0
            team_dict = {}
            for x in range(0, len(columns)):
                if columns[x] == "Team Name":
                    team_dict[columns[x]] = team.name
                    count += 1
                elif columns[x] == "Current Score":
                    team_dict[columns[x]] = team.current_score
                    count += 1
                else:
                    service = session.query(Service).filter(Service.name == columns[x]).filter(
                        Service.team == team).first()
                    service_text = service.host
                    if str(service.port) != '0':
                        service_text += ':' + str(service.port)
                    service_text += ' - ' + str(service.last_check_result())
                    team_dict[columns[x]] = service_text
            data.append(team_dict)
        columnlist = []
        for column in columns:
            columnlist.append({'title': column, 'data': column})
        return json.dumps({'columns': columnlist, 'data': data})
    else:
        return '{}'
