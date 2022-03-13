from flask import jsonify
from flask_login import current_user, login_required

from scoring_engine.db import session
from scoring_engine.models.notifications import Notification

from . import mod


@mod.route("/api/notifications")
@login_required
def home():
    notifications = session.query(Notification).order_by(Notification.id.desc()).all()
    return jsonify(notifications)
