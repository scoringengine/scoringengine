from collections import defaultdict
from flask import request, jsonify
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import desc
from sqlalchemy.sql import case, func

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

from . import make_cache_key, mod


@mod.route("/api/stats")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def api_stats():
    team = session.query(Team).get(current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_blue_team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    if current_user.is_blue_team:
        stats = []
        # TODO - There has to be a better way to subquery this...
        last_round = Round.get_last_round_num()
        res = (
            session.query(
                Round.id.label("round_id"),
                Round.round_start,
                Round.round_end,
                func.sum(case([(Check.result == True, 1)], else_=0)).label("num_successful_checks"),
                func.sum(case([(Check.result == False, 1)], else_=0)).label("num_unsuccessful_checks"),
            )
            .outerjoin(Check, Round.id == Check.round_id)
            .join(Service, Check.service_id == Service.id)  # Ensure checks are linked to services
            .filter(Round.id <= last_round)
            .filter(Service.team_id == team.id)  # Limit results to the specified team
            .group_by(Round.id, Round.round_start, Round.round_end)
            .order_by(Round.id.desc())
            .all()
        )
        for row in res:
            stats.append(
                {
                    "round_id": row[0],
                    "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "total_seconds": (row[2] - row[1]).seconds,
                    "num_up_services": row[3],
                    "num_down_services": row[4],
                }
            )
        return jsonify(data=stats)

    if current_user.is_white_team:
        stats = []
        # TODO - There's probably a better way to do this.
        # session.query(Round.id, func.count(Check.result)).join(Check).join(Service).filter(Check.result.is_(False)).group_by(Round.id).all()
        last_round = Round.get_last_round_num()
        res = (
            session.query(
                Round.id.label("round_id"),
                Round.round_start,
                Round.round_end,
                func.sum(case([(Check.result == True, 1)], else_=0)).label("num_successful_checks"),
                func.sum(case([(Check.result == False, 1)], else_=0)).label("num_unsuccessful_checks"),
            )
            .outerjoin(Check, Round.id == Check.round_id)  # Include all rounds even if no checks are present
            .filter(Round.id <= last_round)
            .group_by(Round.id, Round.round_start, Round.round_end)
            .order_by(desc(Round.id))
            .all()
        )

        for row in res:
            stats.append(
                {
                    "round_id": row[0],
                    "start_time": row[1].astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "end_time": row[2].astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "total_seconds": (row[2] - row[1]).seconds,
                    "num_up_services": row[3],
                    "num_down_services": row[4],
                }
            )
        return jsonify(data=stats)

    return {"status": "Unauthorized"}, 403
