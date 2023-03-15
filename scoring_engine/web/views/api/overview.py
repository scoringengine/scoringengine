import ranking

from collections import defaultdict
from flask import jsonify
from sqlalchemy import desc
from sqlalchemy.sql import func

from scoring_engine.models.check import Check
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team

from scoring_engine.cache import cache
from scoring_engine.db import session

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
    data = defaultdict(lambda: defaultdict(dict))

    round_obj = session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        checks = (
            session.query(Check.service_id, Check.result)
            .join(Round)
            .filter(Round.number == round_obj.number)
            .subquery()
        )
        res = (
            session.query(
                Team.name, Service.name, Service.host, Service.port, checks.c.result
            )
            .join(Team)
            .filter(checks.c.service_id == Service.id)
            .all()
        )

        for r in res:
            data[r[0]][r[1]] = {
                "host": r[2],
                "port": r[3],
                "passing": r[4],
            }

    return jsonify(data)


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
            session.query(Team.id).filter(Team.color == "Blue").order_by(Team.id).all()
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

    num_down_services = dict(
        session.query(
            Service.team_id,
            func.count(Service.team_id),
        )
        .join(Check)
        .join(Round)
        .filter(Check.result.is_(False))
        .filter(Round.number == last_round)
        .group_by(Service.team_id)
        .all()
    )

    if len(blue_team_ids) > 0:
        # TODO - This could explode if the first team has a different number of services than everyone else
        # total_services = (
        #     session.query(Service.id)
        #     .filter(Service.team_id == blue_team_ids[0])
        #     .count()
        # )

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
            # num_up_services, num_down_services = Round.get_round_stats(blue_team_id, last_round)
            current_scores.append(str(team_scores.get(blue_team_id, 0)))
            current_places.append(str(ranks_dict.get(blue_team_id, 0)))
            service_ratios.append(
                # '{0} <span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span> / {1} <span class="glyphicon glyphicon-chevron-down" aria-hidden="true"></span>'.format(num_up_services, num_down_services)  # TODO - I don't like shimming html into this
                '{0} <span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span> / {1} <span class="glyphicon glyphicon-chevron-down" aria-hidden="true"></span>'.format(
                    num_up_services.get(blue_team_id, 0),
                    num_down_services.get(blue_team_id, 0),
                )  # TODO - I don't like shimming html into this
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
