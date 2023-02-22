from flask import request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc
from sqlalchemy.sql import func

import html
import pytz

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.db import session
from scoring_engine.cache_helper import (
    update_overview_data,
    update_services_data,
    update_service_data,
)
from scoring_engine.models.account import Account
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team

from . import mod


@mod.route("/api/stats")
@login_required
@cache.memoize()
def api_stats():
    team = session.query(Team).get(current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_blue_team or current_user.is_white_team):
        return {"status": "Unauthorized"}, 403

    if current_user.is_blue_team:
        stats = []
        # TODO - There has to be a better way to subquery this...
        res = session.query(Check.round_id, func.min(Check.completed_timestamp), func.max(Check.completed_timestamp)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
        num_up_services = session.query(func.count(Check.round_id)).join(Service).filter(Check.result.is_(True)).filter(Service.team_id == team.id).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
        num_down_services = session.query(func.count(Check.round_id)).join(Service).filter(Check.result.is_(False)).filter(Service.team_id == team.id).group_by(Check.round_id).order_by(desc(Check.round_id)).all()

        for index, row in enumerate(res):
            stats.append(
                {
                    "round_id": row[0],
                    "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "total_seconds": (row[2] - row[1]).seconds,
                    "num_up_services": num_up_services[index][0],
                    "num_down_services": num_down_services[index][0],
                }
            )
        return jsonify(data=stats)

    if current_user.is_white_team:
        stats = []
        # TODO - There's probably a better way to do this.
        # session.query(Round.id, func.count(Check.result)).join(Check).join(Service).filter(Check.result.is_(False)).group_by(Round.id).all()
        res = session.query(Check.round_id, func.min(Check.completed_timestamp), func.max(Check.completed_timestamp)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
        num_up_services = session.query(func.count(Check.round_id)).filter(Check.result.is_(True)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()
        num_down_services = session.query(func.count(Check.round_id)).filter(Check.result.is_(False)).group_by(Check.round_id).order_by(desc(Check.round_id)).all()

        for index, row in enumerate(res):
            stats.append(
                {
                    "round_id": row[0],
                    "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "total_seconds": (row[2] - row[1]).seconds,
                    "num_up_services": num_up_services[index][0],
                    "num_down_services": num_down_services[index][0],
                }
            )
        return jsonify(data=stats)
