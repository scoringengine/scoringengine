import os
import uuid
from datetime import datetime, timezone

import pytz
from flask import abort, g, jsonify, request, send_file
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.models.inject import Inject, InjectComment, InjectFile, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.notifications import notify_inject_comment, notify_inject_submitted

from . import make_cache_key, mod


def _utcnow_for_comparison(db_datetime):
    """Get current UTC time, converting to naive if db_datetime is naive (e.g., SQLite)."""
    now = datetime.now(timezone.utc)
    if db_datetime is not None and db_datetime.tzinfo is None:
        return now.replace(tzinfo=None)
    return now


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    return dt.astimezone(pytz.utc)


@mod.route("/api/injects")
@login_required
def api_injects():
    team = db.session.get(Team, current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_blue_team or current_user.is_red_team):
        return jsonify({"status": "Unauthorized"}), 403
    data = list()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    injects = (
        db.session.query(Inject)
        .options(joinedload(Inject.template).joinedload(Template.rubric_items))
        .join(Template)
        .filter(Inject.team == team)
        .filter(Inject.enabled == True)  # noqa: E712
        .filter(Template.start_time < now_naive)
        .all()
    )
    for inject in injects:
        data.append(
            dict(
                id=inject.id,
                template_id=inject.template.id,
                title=inject.template.title,
                score=inject.score,
                max_score=inject.template.max_score,
                status=inject.status,
                start_time=inject.template.start_time,
                end_time=inject.template.end_time,
            )
        )
    return jsonify(data=data)


@mod.route("/api/inject/<inject_id>/submit", methods=["POST"])
@login_required
def api_injects_submit(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403
    if _utcnow_for_comparison(inject.template.end_time) > inject.template.end_time:
        return jsonify({"status": "Inject has ended"}), 403
    if inject.status != "Draft":
        return jsonify({"status": "Inject cannot be submitted in current state"}), 400
    inject.status = "Submitted"
    inject.submitted = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    cache.delete(f"/api/inject/{inject_id}_{g.user.team.id}")
    notify_inject_submitted(inject)

    return jsonify(data=[])


@mod.route("/api/inject/<inject_id>/resubmit", methods=["POST"])
@login_required
def api_injects_resubmit(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403
    if _utcnow_for_comparison(inject.template.end_time) > inject.template.end_time:
        return jsonify({"status": "Inject has ended"}), 403
    if inject.status != "Revision Requested":
        return jsonify({"status": "Inject is not in Revision Requested state"}), 400
    inject.status = "Resubmitted"
    inject.submitted = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    cache.delete(f"/api/inject/{inject_id}_{g.user.team.id}")
    notify_inject_submitted(inject)

    return jsonify(data=[])


@mod.route("/api/inject/<inject_id>/upload", methods=["POST"])
@login_required
def api_injects_file_upload(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403

    if _utcnow_for_comparison(inject.template.end_time) > inject.template.end_time:
        return "Inject has ended", 400
    if inject.status not in ("Draft", "Revision Requested"):
        return "Inject was already submitted", 400
    if not request.files:
        return jsonify({"status": "No file part"}), 400

    files = request.files.getlist("file")
    for file in files:
        original_filename = file.filename
        unique_id = uuid.uuid4().hex[:8]
        filename = "Inject" + str(inject_id) + "_" + current_user.team.name + "_" + unique_id + "_" + secure_filename(file.filename)
        path = os.path.join(config.upload_folder, str(inject.id), current_user.team.name)

        os.makedirs(path, exist_ok=True)
        file.save(os.path.join(path, filename))

        f = InjectFile(filename, current_user, inject, original_filename=original_filename)
        db.session.add(f)
        db.session.commit()

        cache.delete(f"/api/inject/{inject_id}/files_{g.user.team.id}")

    return jsonify({"status": "Inject Submitted Successfully"}), 200


@mod.route("/api/inject/<inject_id>/files/<int:file_id>", methods=["DELETE"])
@login_required
def api_inject_delete_file(inject_id, file_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403
    if inject.status not in ("Draft", "Revision Requested"):
        return jsonify({"status": "Cannot delete files in current state"}), 400

    file_obj = (
        db.session.query(InjectFile)
        .filter(
            InjectFile.id == file_id,
            InjectFile.inject_id == int(inject_id),
        )
        .one_or_none()
    )
    if file_obj is None:
        return jsonify({"status": "File not found"}), 404

    # Try to delete the physical file
    path = os.path.join(config.upload_folder, str(inject.id), inject.team.name, file_obj.filename)
    try:
        os.remove(path)
    except OSError:
        pass

    db.session.delete(file_obj)
    db.session.commit()

    cache.delete(f"/api/inject/{inject_id}/files_{g.user.team.id}")
    cache.delete(f"/api/inject/{inject_id}_{g.user.team.id}")

    return jsonify({"status": "File deleted"}), 200


@mod.route("/api/inject/<inject_id>")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    data = {}

    data["score"] = inject.score
    data["max_score"] = inject.template.max_score
    data["status"] = inject.status

    # Rubric items
    data["rubric_items"] = [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "points": item.points,
        }
        for item in inject.template.rubric_items
    ]

    # Rubric scores
    data["rubric_scores"] = [
        {
            "rubric_item_id": rs.rubric_item_id,
            "score": rs.score,
        }
        for rs in inject.rubric_scores
    ]

    # Comments
    comments = (
        db.session.query(InjectComment)
        .options(joinedload(InjectComment.user).joinedload(User.team))
        .filter(InjectComment.inject == inject)
        .order_by(InjectComment.created)
        .all()
    )
    data["comments"] = [
        {
            "id": comment.id,
            "text": comment.content,
            "user": comment.user.username,
            "team": comment.user.team.name,
            "added": _ensure_utc_aware(comment.created)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z"),
        }
        for comment in comments
    ]

    # Files
    files = (
        db.session.query(InjectFile.id, InjectFile.filename)
        .filter(InjectFile.inject_id == inject_id)
        .order_by(InjectFile.filename)
        .all()
    )
    data["files"] = [{"id": file[0], "name": file[1]} for file in files]

    return jsonify(data), 200


@mod.route("/api/inject/<inject_id>/comments")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject_comments(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    data = []
    comments = (
        db.session.query(InjectComment)
        .options(joinedload(InjectComment.user).joinedload(User.team))
        .filter(InjectComment.inject == inject)
        .order_by(InjectComment.created)
        .all()
    )
    for comment in comments:
        data.append(
            {
                "id": comment.id,
                "text": comment.content,
                "user": comment.user.username,
                "team": comment.user.team.name,
                "added": _ensure_utc_aware(comment.created)
                .astimezone(pytz.timezone(config.timezone))
                .strftime("%Y-%m-%d %H:%M:%S %Z"),
            }
        )

    return jsonify(data=data), 200


@mod.route("/api/inject/<inject_id>/comment", methods=["POST"])
@login_required
def api_inject_add_comment(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403
    if _utcnow_for_comparison(inject.template.end_time) > inject.template.end_time:
        return jsonify({"status": "Inject has ended"}), 400

    data = request.get_json()
    if "comment" not in data or data["comment"] == "":
        return jsonify({"status": "No comment"}), 400

    c = InjectComment(data["comment"], current_user, inject)
    db.session.add(c)
    db.session.commit()

    cache.delete(f"/api/inject/{inject_id}/comments_{g.user.team.id}")
    cache.delete(f"/api/inject/{inject_id}_{g.user.team.id}")
    notify_inject_comment(inject, current_user)

    return jsonify({"status": "Comment added"}), 200


@mod.route("/api/inject/<inject_id>/files")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject_files(inject_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    files = (
        db.session.query(InjectFile.id, InjectFile.filename)
        .filter(InjectFile.inject_id == inject_id)
        .order_by(InjectFile.filename)
        .all()
    )

    if files is None:
        return jsonify({"status": "Unauthorized"}), 403

    data = []
    for file in files:
        data.append({"id": file[0], "name": file[1]})

    return jsonify(data=data)


@mod.route("/api/inject/<inject_id>/files/<file_id>/download")
@login_required
def api_inject_download(inject_id, file_id):
    inject = db.session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    file = db.session.query(InjectFile).filter(InjectFile.id == file_id).one_or_none()

    if file is None:
        return jsonify({"status": "Unauthorized"}), 403

    path = os.path.join(config.upload_folder, str(inject.id), inject.team.name, file.filename)
    try:
        return send_file(path, as_attachment=True)
    except FileNotFoundError:
        abort(404)
