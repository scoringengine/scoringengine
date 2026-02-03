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

    # Get per-announcement read status
    read_ids = set()
    if user and user.is_authenticated:
        read_ids = AnnouncementRead.get_read_announcement_ids(
            db.session, user.id
        )

    has_unread = any(a.id not in read_ids for a in visible_announcements) if user and user.is_authenticated else len(visible_announcements) > 0

    return render_template(
        "announcements.html",
        announcements=visible_announcements,
        read_ids=read_ids,
        has_unread=has_unread,
    )
