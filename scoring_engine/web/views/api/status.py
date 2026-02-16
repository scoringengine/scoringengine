from datetime import datetime

from flask import jsonify
from flask_login import current_user, login_required

from scoring_engine.db import db
from scoring_engine.models.machines import Machine

from . import mod


def _serialize_machine(machine):
    """Return every Machine model field as JSON-safe data."""
    data = {}
    for column in Machine.__table__.columns:
        value = getattr(machine, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        data[column.name] = value
    return data


@mod.route("/api/status")
@login_required
def api_status():
    # White and Red can see all machines.
    if current_user.is_white_team or current_user.is_red_team:
        machines = db.session.query(Machine).order_by(Machine.name).all()
    # Blue can only see their own team's machines.
    elif current_user.is_blue_team:
        machines = (
            db.session.query(Machine)
            .filter(Machine.team_id == current_user.team.id)
            .order_by(Machine.name)
            .all()
        )
    else:
        return {"status": "Unauthorized"}, 403

    return jsonify(data=[_serialize_machine(machine) for machine in machines])