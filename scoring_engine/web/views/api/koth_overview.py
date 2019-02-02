import json
from flask import jsonify

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round

from . import mod


ROUNDS_DISPLAYED = 5


def get_table_columns():
    rounds = Round.get_previous_rounds(ROUNDS_DISPLAYED)
    columns = []
    columns.append({'title': '', 'data':''})
    for round in rounds:
        columns.append({'title': round.number, 'data': round.number})
    return columns


@mod.route('/api/koth_overview/get_round_data')
@cache.memoize()
def koth_overview_get_round_data():
    round_obj = session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        round_start = round_obj.local_round_start
        number = round_obj.number
    else:
        round_start = ""
        number = 0
    data = {'round_start': round_start, 'number': number}
    return jsonify(data)


@mod.route('/api/koth_overview/data')
@cache.memoize()
def koth_overview_data():
    round_data = {}
    rounds = Round.get_previous_rounds(ROUNDS_DISPLAYED)
    for round in rounds:
        service_data = {}
        services = session.query(Service).filter(Service.name.like('KOTH-%')).all()
        for service in services:
            service_data[service.name] = {
                'passing': service.check_result_for_round(round.number),
                'ownership': service.ownership_for_round(round.number).name,
                'host': service.host,
                'port': service.port,
            }
        round_data[round.number] = service_data
    return jsonify(round_data)


@mod.route('/api/koth_overview/get_columns')
@cache.memoize()
def koth_overview_get_columns():
    return jsonify(columns=get_table_columns())


@mod.route('/api/koth_overview/get_data')
@cache.memoize()
def koth_overview_get_data():
    columns = get_table_columns()
    data = []
    rounds = Round.get_previous_rounds(ROUNDS_DISPLAYED)

    if len(rounds) > 0:
        services = session.query(Service).filter(Service.name.like('KOTH-%')).all()
        for service in services:
            service_row_data = {'': service.name}
            for round in rounds:
                service_text = service.host
                if str(service.port) != '0':
                    service_text += ':' + str(service.port)
                service_data = {
                    'result': str(service.check_result_for_round(round.number)),
                    'host_info': service_text,
                    'ownership': str(service.ownership_for_round(round.number).name),
                }
                service_row_data[round.number] = service_data
            data.append(service_row_data)

        # FIXME: jsonify this so it appears as json, not raw text
        return json.dumps({'columns': columns, 'data': data})
    else:
        return '{}'
