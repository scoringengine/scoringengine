from dateutil.parser import parse
from flask import jsonify, request
from flask_login import current_user, login_required

from scoring_engine.cache import cache
from scoring_engine.cache_helper import update_announcements_data
from scoring_engine.db import db
from scoring_engine.models.announcement import Announcement
from scoring_engine.models.team import Team

from . import mod


def _announcements_cache_key_prefix():
    """Cache key prefix based on user visibility context."""
    if not current_user.is_authenticated:
        return "anonymous"
    if current_user.is_white_team:
        return "white"
    if current_user.is_red_team:
        return "red"
    return f"team_{current_user.team.id}"


def _announcements_cache_key():
    return f"/api/announcements_{_announcements_cache_key_prefix()}"


def _announcements_ids_cache_key():
    return f"/api/announcements/ids_{_announcements_cache_key_prefix()}"


def _get_visible_announcements():
    """Query visible announcements for the current user (uncached helper)."""
    user = current_user if current_user.is_authenticated else None
    announcements = (
        db.session.query(Announcement)
        .filter(Announcement.is_active.is_(True))
        .order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()
        )
        .all()
    )
    return [a for a in announcements if a.is_visible_to_user(user)]


@mod.route("/api/announcements")
@cache.cached(make_cache_key=_announcements_cache_key)
def get_announcements():
    """
    Get all announcements visible to the current user.
    Full data - only used on the announcements page.
    """
    visible = _get_visible_announcements()
    return jsonify(data=[a.to_dict() for a in visible])


@mod.route("/api/announcements/count")
@cache.cached(make_cache_key=_announcements_ids_cache_key)
def get_announcement_count():
    """
    Get IDs of visible announcements.
    Lightweight endpoint for badge polling - client computes
    unread count by diffing against localStorage read IDs.
    """
    visible = _get_visible_announcements()
    return jsonify(ids=[a.id for a in visible])


@mod.route("/api/admin/announcements", methods=["GET"])
@login_required
def admin_get_announcements():
    """Get all announcements for admin view (includes inactive)."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcements = (
        db.session.query(Announcement)
        .order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()
        )
        .all()
    )

    return jsonify(data=[a.to_dict() for a in announcements])


@mod.route("/api/admin/announcements", methods=["POST"])
@login_required
def admin_create_announcement():
    """Create a new announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json()

    if not data.get("title") or not data.get("content"):
        return jsonify({
            "status": "Error",
            "message": "Title and content are required",
        }), 400

    announcement = Announcement(
        title=data["title"],
        content=data["content"],
        audience=data.get("audience", "global"),
        author_id=current_user.id,
    )

    if data.get("is_pinned"):
        announcement.is_pinned = True

    if data.get("expires_at"):
        try:
            announcement.expires_at = parse(data["expires_at"])
        except (ValueError, TypeError):
            pass

    db.session.add(announcement)
    db.session.commit()
    update_announcements_data()

    return jsonify({"status": "Success", "data": announcement.to_dict()}), 201


@mod.route("/api/admin/announcements/<int:announcement_id>", methods=["GET"])
@login_required
def admin_get_announcement(announcement_id):
    """Get a specific announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcement = db.session.get(Announcement, announcement_id)
    if not announcement:
        return jsonify({
            "status": "Error",
            "message": "Announcement not found",
        }), 404

    return jsonify(data=announcement.to_dict())


@mod.route("/api/admin/announcements/<int:announcement_id>", methods=["PUT"])
@login_required
def admin_update_announcement(announcement_id):
    """Update an existing announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcement = db.session.get(Announcement, announcement_id)
    if not announcement:
        return jsonify({
            "status": "Error",
            "message": "Announcement not found",
        }), 404

    data = request.get_json()

    if data.get("title"):
        announcement.title = data["title"]

    if data.get("content"):
        announcement.content = data["content"]

    if "audience" in data:
        announcement.audience = data["audience"]

    if "is_pinned" in data:
        announcement.is_pinned = bool(data["is_pinned"])

    if "is_active" in data:
        announcement.is_active = bool(data["is_active"])

    if "expires_at" in data:
        if data["expires_at"]:
            try:
                announcement.expires_at = parse(data["expires_at"])
            except (ValueError, TypeError):
                pass
        else:
            announcement.expires_at = None

    db.session.add(announcement)
    db.session.commit()
    update_announcements_data()

    return jsonify({"status": "Success", "data": announcement.to_dict()})


@mod.route("/api/admin/announcements/<int:ann_id>", methods=["DELETE"])
@login_required
def admin_delete_announcement(ann_id):
    """Delete an announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcement = db.session.get(Announcement, ann_id)
    if not announcement:
        return jsonify({
            "status": "Error",
            "message": "Announcement not found",
        }), 404

    db.session.delete(announcement)
    db.session.commit()
    update_announcements_data()

    return jsonify({"status": "Success"})


@mod.route(
    "/api/admin/announcements/<int:ann_id>/toggle_pin", methods=["POST"]
)
@login_required
def admin_toggle_pin_announcement(ann_id):
    """Toggle the pinned status of an announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcement = db.session.get(Announcement, ann_id)
    if not announcement:
        return jsonify({
            "status": "Error",
            "message": "Announcement not found",
        }), 404

    announcement.is_pinned = not announcement.is_pinned
    db.session.add(announcement)
    db.session.commit()
    update_announcements_data()

    return jsonify({"status": "Success", "is_pinned": announcement.is_pinned})


@mod.route(
    "/api/admin/announcements/<int:ann_id>/toggle_active", methods=["POST"]
)
@login_required
def admin_toggle_active_announcement(ann_id):
    """Toggle the active status of an announcement."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    announcement = db.session.get(Announcement, ann_id)
    if not announcement:
        return jsonify({
            "status": "Error",
            "message": "Announcement not found",
        }), 404

    announcement.is_active = not announcement.is_active
    db.session.add(announcement)
    db.session.commit()
    update_announcements_data()

    return jsonify({"status": "Success", "is_active": announcement.is_active})


@mod.route("/api/admin/teams/list")
@login_required
def admin_get_teams_list():
    """Get list of teams for announcement targeting."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    teams = db.session.query(Team).all()
    team_list = [{"id": t.id, "name": t.name, "color": t.color} for t in teams]

    return jsonify(data=team_list)
