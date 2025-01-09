import ranking

from collections import defaultdict
from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc, func
from sqlalchemy.orm import subqueryload

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import make_cache_key, mod


@mod.route("/api/team/<team_id>/stats")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def services_get_team_data(team_id):
    team = session.query(Team).get(team_id)
    if team is None or not current_user.team == team or not current_user.is_blue_team:
        return {"status": "Unauthorized"}, 403

    data = {"place": str(team.place), "current_score": str(team.current_score)}
    return jsonify(data)


@mod.route("/api/team/<team_id>/services")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_services(team_id):
    team = session.query(Team).get(team_id)
    if team is None or not current_user.team == team or not current_user.is_blue_team:
        return {"status": "Unauthorized"}, 403

    data = []

    # Do math for ranks here per service
    service_scores = (
        session.query(Service.team_id, Service.name, func.sum(Service.points).label("score"))
        .join(Check)
        .filter(Check.result.is_(True))
        .group_by(Service.team_id, Service.name)
        .order_by(Service.name, desc("score"))
        .all()
    )

    service_dict = defaultdict(lambda: defaultdict(list))

    for team_id, name, points in service_scores:
        service_dict[name][team_id] = points

    service_ranks = defaultdict(lambda: defaultdict(int))

    for service in service_dict.keys():
        ranks = list(ranking.Ranking(service_dict[service].values(), start=1).ranks())  # [1, 2, 2, 4, 5]
        service_ranks[service] = dict(
            zip(service_dict[service].keys(), ranks)
        )  # {12: 1, 3: 2, 10: 3, 4: 4, 7: 5, 5: 6, 6: 7, 11: 8, 9: 9, 8: 10}

    services = (
        session.query(Service)
        .options(subqueryload(Service.checks))
        .options(subqueryload(Service.team))
        .filter(Service.team_id == team.id)
        .order_by(Service.id)
        .all()
    )

    for service in services:
        score_earned = str(service_dict[service.name].get(service.team_id, 0))
        max_score = str(len(service.checks) * service.points)
        percent_earned = "{:.1%}".format(int(score_earned) / int(max_score) if int(max_score) != 0 else 0)

        if not service.checks:
            check = "Undetermined"
        else:
            if service.last_check_result():
                check = "UP"
            else:
                check = "DOWN"
        data.append(
            dict(
                service_id=str(service.id),
                service_name=str(service.name),
                host=str(service.host),
                port=str(service.port),
                check=str(check),
                rank=str(service_ranks[service.name].get(service.team_id, 1)),
                score_earned=score_earned,
                max_score=max_score,
                percent_earned=percent_earned,
                pts_per_check=str(service.points),
                last_ten_checks=[check.result for check in service.last_ten_checks[::-1]],
            )
        )
    return jsonify(data=data)


@mod.route("/api/team/<team_id>/services/status")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def team_services_status(team_id):
    team = session.query(Team).get(team_id)
    if team is None or not current_user.team == team or not current_user.is_blue_team:
        return {"status": "Unauthorized"}, 403

    data = {}

    round_id = session.query(Round.id).order_by(Round.number.desc()).first()[0]

    # We have no round data, the first round probably hasn't started yet
    if not round_id:
        return data

    checks = (
        session.query(
            Service.name,
            Check.service_id,
            Check.result,
        )
        .select_from(Check)
        .join(Service)
        .filter(Service.team_id == team_id)
        .filter(Check.round_id == round_id)
        .order_by(Service.name)
        .all()
    )

    for service_name, service_id, check_result in checks:
        data[service_name] = {
            "id": str(service_id),
            "result": str(check_result),
        }
    return jsonify(data)
