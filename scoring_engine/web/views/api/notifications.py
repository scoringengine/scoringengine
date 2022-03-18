import pytz

from flask import jsonify
from flask_login import current_user, login_required

from scoring_engine.config import config
from scoring_engine.db import session
from scoring_engine.models.notifications import Notification

from . import mod


@mod.route("/api/notifications")
@login_required
def api_notifications():
    notifications = (
        session.query(Notification)
        .filter(Notification.team_id == current_user.team_id)
        .order_by(Notification.id.desc())
        .all()
    )
    data = []
    for notification in notifications:
        print(notification.__dict__)
        data.append(
            {
                "id": notification.id,
                "message": notification.message,
                "target": notification.target,
                "is_read": notification.is_read,
                "created": notification.created.astimezone(
                    pytz.timezone(config.timezone)
                ).strftime("%Y-%m-%d %H:%M:%S %Z"),
            }
        )
    return jsonify(data)


@mod.route("/api/notifications/read")
@login_required
def api_notifications_read():
    notifications = (
        session.query(Notification)
        .filter(Notification.team_id == current_user.team_id)
        .filter(Notification.is_read == False)
        .order_by(Notification.id.desc())
        .all()
    )
    data = []
    for notification in notifications:
        print(notification.__dict__)
        data.append(
            {
                "id": notification.id,
                "message": notification.message,
                "target": notification.target,
                "created": notification.created.astimezone(
                    pytz.timezone(config.timezone)
                ).strftime("%Y-%m-%d %H:%M:%S %Z"),
            }
        )
    return jsonify(data)


@mod.route("/api/notifications/unread")
@login_required
def api_notifications_unread():
    notifications = (
        session.query(Notification)
        .filter(Notification.team_id == current_user.team_id)
        .filter(Notification.is_read == False)
        .order_by(Notification.id.desc())
        .all()
    )
    data = []
    for notification in notifications:
        print(notification.__dict__)
        data.append(
            {
                "id": notification.id,
                "message": notification.message,
                "target": notification.target,
                "created": notification.created.astimezone(
                    pytz.timezone(config.timezone)
                ).strftime("%Y-%m-%d %H:%M:%S %Z"),
            }
        )
    return jsonify(data)
