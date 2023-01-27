from flask import Blueprint, render_template

from scoring_engine.db import session
from scoring_engine.models.notifications import Notification

mod = Blueprint("notifications", __name__)


@mod.route("/notifications")
@mod.route("/notifications/unread")
def unread():
    # notification_count = session.query(Notification).filter(current_user).all()
    return render_template("notifications.html", notification_count=1)


@mod.route("/notifications/read")
def read():
    return render_template("notifications.html", notification_count=1)
