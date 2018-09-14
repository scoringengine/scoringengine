import json
from collections import OrderedDict
from flask import jsonify

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.models.setting import Setting

from . import mod


def get_table_columns():
    blue_teams = Team.get_all_blue_teams()
    columns = []
    columns.append({'title': '', 'data': ''})
    for team in blue_teams:
        columns.append({'title': team.name, 'data': team.name})
    return columns


@mod.route('/api/overview/get_round_data')
@cache.memoize()
def overview_get_round_data():
    if Setting.get_setting('overview_show_round_info').value is False:
        return jsonify({'status': 'Unauthorized'})
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
    return jsonify(columns=get_table_columns())


@mod.route('/api/overview/get_data')
@cache.memoize()
def overview_get_data():
    columns = get_table_columns()
    data = []
    blue_teams = Team.get_all_blue_teams()

    if len(blue_teams) > 0:
        current_score_row_data = {'': 'Current Score'}
        current_place_row_data = {'': 'Current Place'}
        for blue_team in blue_teams:
            current_score_row_data[blue_team.name] = blue_team.current_score
            current_place_row_data[blue_team.name] = blue_team.place
        data.append(current_score_row_data)
        data.append(current_place_row_data)

        for service in blue_teams[0].services:
            service_row_data = {'': service.name}
            for blue_team in blue_teams:
                service = session.query(Service).filter(Service.name == service.name).filter(Service.team == blue_team).first()
                service_text = service.host
                if str(service.port) != '0':
                    service_text += ':' + str(service.port)
                service_data = {
                    'result': str(service.last_check_result()),
                    'host_info': service_text
                }
                service_row_data[blue_team.name] = service_data
            data.append(service_row_data)

        return json.dumps({'columns': columns, 'data': data})
    else:
        return '{}'
