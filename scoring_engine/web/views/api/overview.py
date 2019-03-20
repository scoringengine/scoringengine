import json
from flask import jsonify
from sqlalchemy import func

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.pwnboard import Pwnboard
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

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
    team_data = {}
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
    return jsonify(team_data)


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
        current_up_down_row_data = {'': 'Up/Down Ratio'}
        red_team_score = {'': 'Red Team Score'}  # Red Team Score
        for blue_team in blue_teams:
            current_score_row_data[blue_team.name] = blue_team.current_score
            current_place_row_data[blue_team.name] = blue_team.place
            red_team_score[blue_team.name] = 0  # Red Team Score
            num_up_services = 0
            num_down_services = 0
            for service in blue_team.services:
                service_result = service.last_check_result()
                if service_result is True:
                    num_up_services += 1
                elif service_result is False:
                    num_down_services += 1
                # Red Team Score
                year = func.extract('year', Pwnboard.timestamp).label('year')
                month = func.extract('month', Pwnboard.timestamp).label('month')
                day = func.extract('day', Pwnboard.timestamp).label('day')
                hour = func.extract('hour', Pwnboard.timestamp).label('hour')
                session.query(func.count(Pwnboard.id))\
                    .join(User)\
                    .filter(Pwnboard.service == service)\
                    .group_by(Pwnboard.user, year, month, day, hour)\
                    .count()
                red_team_score[blue_team.name] += session.query(func.min(Pwnboard.timestamp).label('timestamp'),
                                                                func.count(Pwnboard.timestamp))\
                    .join(User)\
                    .filter(Pwnboard.service == service)\
                    .group_by(User, func.date_format(Pwnboard.timestamp, "%Y-%m-%d %H"))\
                    .count()
                '''
                red_team_score[blue_team.name] += session.query(Pwnboard) \
                    .filter(Pwnboard.service == service) \
                    .group_by(func.year(Pwnboard.timestamp), func.month(Pwnboard.timestamp),
                              func.day(Pwnboard.timestamp), func.hour(Pwnboard.timestamp)) \
                    .count()
                '''
            current_up_down_row_data[blue_team.name] = "{0} / {1}".format(num_up_services, num_down_services)
        data.append(current_score_row_data)
        data.append(current_place_row_data)
        data.append(current_up_down_row_data)
        data.append(red_team_score)  # Red Team Score

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
