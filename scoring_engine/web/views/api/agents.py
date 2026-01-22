from flask import jsonify

from scoring_engine.models.check import Check
from scoring_engine.models.service import Service
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team

from scoring_engine.cache import cache
from scoring_engine.db import db

from . import mod


def get_agent_table_columns():
    blue_teams = Team.get_all_blue_teams()
    columns = []
    columns.append({"title": "", "data": ""})
    for team in blue_teams:
        columns.append({"title": team.name, "data": team.name})
    return columns


@mod.route("/api/agents/get_columns")
@cache.memoize()
def agents_get_columns():
    return jsonify(columns=get_agent_table_columns())


@mod.route("/api/agents/get_data")
@cache.memoize()
def agents_get_data():
    data = []
    blue_team_ids = [
        team_id[0]
        for team_id in (
            db.session.query(Team.id).filter(Team.color == "Blue").order_by(Team.id).all()
        )
    ]
    last_round = Round.get_last_round_num()

    if len(blue_team_ids) == 0 or last_round == 0:
        return jsonify(data=[])

    # Query all AgentCheck services and their latest check results
    # Get checks for the last round where check_name is 'AgentCheck'
    checks = (
        db.session.query(Service.host, Service.team_id, Check.result)
        .join(Check, Check.service_id == Service.id)
        .filter(Service.check_name == "AgentCheck")
        .filter(Check.round_id == last_round)
        .order_by(Service.host, Service.team_id)
        .all()
    )

    # Build a dict mapping (host, team_id) -> result
    results_dict = {}
    hosts_set = set()
    for host, team_id, result in checks:
        results_dict[(host, team_id)] = result
        hosts_set.add(host)

    # Sort hosts for consistent display
    hosts = sorted(hosts_set)

    # Build data rows: each row is [host, result_team1, result_team2, ...]
    for host in hosts:
        row = [host]
        for team_id in blue_team_ids:
            # Get result for this host and team, default to None if no agent configured
            result = results_dict.get((host, team_id))
            row.append(result)
        data.append(row)

    return jsonify(data=data)
