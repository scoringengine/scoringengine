from flask import jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc, func

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import mod


@mod.route("/api/team/<team_id>/stats")
@login_required
@cache.memoize()
def services_get_team_data(team_id):
    team = session.query(Team).get(team_id)
    if team is None or not current_user.team == team or not current_user.is_blue_team:
        return {"status": "Unauthorized"}, 403

    data = {"place": str(team.place), "current_score": str(team.current_score)}
    return jsonify(data)


@mod.route("/api/team/<team_id>/services")
@login_required
@cache.memoize()
def api_services(team_id):
    team = session.query(Team).get(team_id)
    if team is None or not current_user.team == team or not current_user.is_blue_team:
        return {"status": "Unauthorized"}, 403

    data = []

    services = (
        session.query(Service)
        .filter(Service.team_id == team.id)
        .order_by(Service.id)
        .all()
    )

    # TODO - Optimize this
    for service in services:
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
                rank=str(service.rank),  # TODO - Optimize this
                score_earned=str(service.score_earned),
                max_score=str(service.max_score),
                percent_earned=str(int(service.score_earned / service.max_score * 100)),
                pts_per_check=str(service.points),
                last_ten_checks=[
                    check.result for check in service.last_ten_checks[::-1]
                ],
            )
        )
    return jsonify(data=data)


@mod.route("/api/team/<team_id>/services/status")
@login_required
@cache.memoize()
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
