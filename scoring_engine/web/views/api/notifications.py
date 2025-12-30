import pytz

from flask import jsonify
from flask_login import current_user, login_required

from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.models.notifications import Notification

from . import mod


def _get_notifications_data(is_read_filter=None, include_is_read=False):
    """Helper function to get notifications data with optional filtering.

    Args:
        is_read_filter: None for all notifications, True for read, False for unread
        include_is_read: Whether to include is_read field in response

    Returns:
        List of notification dictionaries
    """
    query = db.session.query(Notification).filter(Notification.team_id == current_user.team_id)

    if is_read_filter is not None:
        query = query.filter(Notification.is_read == is_read_filter)

    notifications = query.order_by(Notification.id.desc()).all()

    data = []
    for notification in notifications:
        notification_dict = {
            "id": notification.id,
            "message": notification.message,
            "target": notification.target,
            "created": notification.created.astimezone(
                pytz.timezone(config.timezone)
            ).strftime("%Y-%m-%d %H:%M:%S %Z"),
        }
        if include_is_read:
            notification_dict["is_read"] = notification.is_read
        data.append(notification_dict)

    return data


@mod.route("/api/notifications")
@login_required
def api_notifications():
    return jsonify(_get_notifications_data(include_is_read=True))


@mod.route("/api/notifications/read")
@login_required
def api_notifications_read():
    return jsonify(_get_notifications_data(is_read_filter=False))


@mod.route("/api/notifications/unread")
@login_required
def api_notifications_unread():
    return jsonify(_get_notifications_data(is_read_filter=False))
