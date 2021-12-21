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
    # columns = get_table_columns()
    data = []
    blue_teams = Team.get_all_blue_teams()
    last_round = Round.get_last_round_num()

    current_scores = ["Current Score"]
    current_places = ["Current Place"]
    service_ratios = ["Up/Down Ratio"]

    if len(blue_teams) > 0:
        for blue_team in blue_teams:
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
                .filter(Check.result.is_(False))
                .filter(Service.team_id == blue_team.id)
                .filter(Round.number == last_round)
                .count()
            )

            current_scores.append(str(blue_team.current_score))
            current_places.append(str(blue_team.place))
            service_ratios.append(
                "{0} / {1}".format(num_up_services, num_down_services)
            )
        data.append(current_scores)
        data.append(current_places)
        data.append(service_ratios)

        services = []
        services.append(
            [
                service[0]
                for service in session.query(Service.name)
                .distinct(Service.name)
                .group_by(Service.name)
                .all()
            ]
        )
        for blue_team in blue_teams:
            checks = (
                session.query(Check.result)
                .join(Service)
                .filter(Check.round_id == last_round)
                .filter(Service.team_id == blue_team.id)
                .order_by(Service.name)
                .all()
            )
            services.append([check[0] for check in checks])
        data += list(zip(*services))  # zip these to get the right datatables format

        return json.dumps({"data": data})
    else:
        return "{}"
