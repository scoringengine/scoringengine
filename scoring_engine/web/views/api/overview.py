import ranking

from collections import defaultdict
from flask import jsonify
from sqlalchemy import desc
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
    blue_team_ids = [
        team_id[0]
        for team_id in (
            session.query(Team.id)
            .filter(Team.color == "Blue")
            .order_by(Team.name)
            .all()
        )
    ]
    last_round = Round.get_last_round_num()

    current_scores = ["Current Score"]
    current_places = ["Current Place"]
    service_ratios = ["Up/Down Ratio"]

    num_up_services = dict(
        session.query(
            Service.team_id,
            func.count(Service.team_id),
        )
        .join(Check)
        .join(Round)
        .filter(Check.result.is_(True))
        .filter(Round.number == last_round)
        .group_by(Service.team_id)
        .all()
    )

    if len(blue_team_ids) > 0:
        # TODO - This could explode if the first team has a different number of services than everyone else
        total_services = (
            session.query(Service.id)
            .filter(Service.team_id == blue_team_ids[0])
            .count()
        )

        team_scores = dict(
            session.query(Service.team_id, func.sum(Service.points).label("score"))
            .join(Check)
            .filter(Check.result.is_(True))
            .group_by(Service.team_id)
            .order_by(desc("score"))
            .all()
        )

        ranks = list(
            ranking.Ranking(team_scores.values(), start=1).ranks()
        )  # [1, 2, 2, 4, 5]
        ranks_dict = dict(
            zip(team_scores.keys(), ranks)
        )  # {12: 1, 3: 2, 10: 3, 4: 4, 7: 5, 5: 6, 6: 7, 11: 8, 9: 9, 8: 10}

        for blue_team_id in blue_team_ids:
            current_scores.append(str(team_scores.get(blue_team_id, 0)))
            current_places.append(str(ranks_dict.get(blue_team_id, 0)))
            service_ratios.append(
                "{0} / {1}".format(num_up_services.get(blue_team_id, 0), total_services)
            )

        data.append(current_scores)
        data.append(current_places)
        data.append(service_ratios)

        checks = (
            session.query(Service.name, Check.result)
            .join(Service)
            .filter(Check.round_id == last_round)
            .order_by(Service.name, Service.team_id)
            .all()
        )

        service_dict = defaultdict(list)

        # Loop through each check and create a default dictionary
        """
        {'SERVICE': [True,
              True,
              False,
              False,
              False,
              False,
              False,
              True,
              False,
              True]
        """
        for service, status in checks:
            service_dict[service].append(status)

        # Loop through dictionary to create datatables formatted list
        for k, v in service_dict.items():
            data.append(
                [k] + v
            )  # ['SERVICE', True, False, False, False, False, False, False, True, False, False]
        return jsonify(data=data)
    else:
        return "{}"
