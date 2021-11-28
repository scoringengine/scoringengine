import json
from flask import jsonify
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team

from . import mod


def get_table_columns():
    blue_teams = Team.get_all_blue_teams()
    columns = []
    columns.append({"title": "", "data": ""})
    for team in blue_teams:
        columns.append({"title": team.name, "data": team.name})
    return columns


@mod.route("/api/overview/get_round_data")
@cache.memoize()
def overview_get_round_data():
    round_obj = session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        round_start = round_obj.local_round_start
        number = round_obj.number
    else:
        round_start = ""
        number = 0
    data = {"round_start": round_start, "number": number}
    return jsonify(data)


@mod.route("/api/overview/data")
@cache.memoize()
def overview_data():
    # services_data = session.query(
    #     Service.team_id,
    #     Service.check_name,
    #     Service.host,
    #     Service.port,
    #     Check.result,
    #     func.max(Check.completed_timestamp),
    # ) \
    # .join(Check) \
    # .group_by(Service.team_id) \
    # .group_by(Service.check_name) \
    # .all()

    team_data = {}
    teams = session.query(Team).filter(Team.color == "Blue").order_by(Team.name).all()
    # teams = session.query(Team.id, Team.name).filter(Team.color == 'Blue').order_by(Team.name).all()
    for team in teams:
        query_data = (
            session.query(
                Service.team_id,
                Team.name,
                Service.name,
                Check.result,
                func.max(Check.completed_timestamp),
                Service.host,
                Service.port,
            )
            .join(Check)
            .join(Team)
            .filter(Service.team_id == team.id)
            .group_by(Service.team_id)
            .group_by(Service.name)
            .all()
        )

        service_data = {
            x[2]: {"host": x[5], "passing": x[3], "port": x[6]} for x in query_data
        }

        # service_data = {}
        # for service in team.services:
        #     service_data[service.name] = {
        #         'passing': service.last_check_result(),
        #         'host': service.host,
        #         'port': service.port,
        #     }
        team_data[team.name] = service_data
    return jsonify(team_data)


@mod.route("/api/overview/get_columns")
@cache.memoize()
def overview_get_columns():
    return jsonify(columns=get_table_columns())


@mod.route("/api/overview/get_data")
@cache.memoize()
def overview_get_data():
    columns = get_table_columns()
    data = []
    blue_teams = Team.get_all_blue_teams()
    last_round = Round.get_last_round_num()

    if len(blue_teams) > 0:
        current_score_row_data = {"": "Current Score"}
        current_place_row_data = {"": "Current Place"}
        current_up_down_row_data = {"": "Up/Down Ratio"}
        for blue_team in blue_teams:
            current_score_row_data[blue_team.name] = blue_team.current_score
            current_place_row_data[blue_team.name] = blue_team.place

            num_up_services = (
                session.query(
                    Service.team_id,
                )
                .join(Check)
                .join(Round)
                .filter(Check.result.is_(True))
                .filter(Service.team_id == blue_team.id)
                .filter(Round.number == last_round)
                .count()
            )

            num_down_services = (
                session.query(
                    Service.team_id,
                )
                .join(Check)
                .join(Round)
                .filter(Service.team_id == blue_team.id)
                .filter(Round.number == last_round)
                .count()
            )

            current_up_down_row_data[blue_team.name] = "{0} / {1}".format(
                num_up_services, num_down_services
            )
        data.append(current_score_row_data)
        data.append(current_place_row_data)
        data.append(current_up_down_row_data)

        # TODO - Optimize this...
        for service in blue_teams[0].services:
            service_row_data = {"": service.name}
            for blue_team in blue_teams:
                service = (
                    session.query(Service)
                    .filter(Service.name == service.name)
                    .filter(Service.team == blue_team)
                    .first()
                )
                service_text = service.host
                if str(service.port) != "0":
                    service_text += ":" + str(service.port)
                service_data = {
                    "result": str(service.last_check_result()),
                    "host_info": service_text,
                }
                service_row_data[blue_team.name] = service_data
            data.append(service_row_data)

        return json.dumps({"columns": columns, "data": data})
    else:
        return "{}"
