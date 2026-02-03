from flask import Blueprint, render_template
from flask_login import current_user

from scoring_engine.db import db
from scoring_engine.models.announcement import Announcement, AnnouncementRead

mod = Blueprint("announcements", __name__)


@mod.route("/announcements")
def home():
    """Display announcements page."""
    user = current_user if current_user.is_authenticated else None

    # Query all active announcements
    announcements = (
        db.session.query(Announcement)
        .filter(Announcement.is_active.is_(True))
        .order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()
        )
        .all()
    )

    # Filter by visibility
    visible_announcements = [
        a for a in announcements if a.is_visible_to_user(user)
    ]

    # Get last read timestamp for highlighting new announcements
    last_read_at = None
    if user and user.is_authenticated:
        read_record = (
            db.session.query(AnnouncementRead)
            .filter(AnnouncementRead.user_id == user.id)
            .first()
        )
        if read_record:
            last_read_at = read_record.last_read_at

    # Count unread announcements
    has_unread = False
    if last_read_at is not None:
        has_unread = any(
            a.created_at and a.created_at > last_read_at
            for a in visible_announcements
        )
    elif user and user.is_authenticated:
        # No read record means all are unread
        has_unread = len(visible_announcements) > 0

    return render_template(
        "announcements.html",
        announcements=visible_announcements,
        last_read_at=last_read_at,
        has_unread=has_unread,
    )
