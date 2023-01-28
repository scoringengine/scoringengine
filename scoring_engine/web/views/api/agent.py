from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import desc, func

from scoring_engine.cache import cache
from scoring_engine.db import session
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import mod


@mod.route("/api/agent/checkin")
def agent_checkin_get():
    return jsonify({})


@mod.route("/api/agent/checkin", methods=["POST"])
def agent_checkin_post():
    data = request.get_json()
    first = data.get('first', False)
    flags = data.get('flags', [])
    timestamp = data.get('timestamp', 0)

    print(data)
    
    return jsonify({})