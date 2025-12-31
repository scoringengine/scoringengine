import os
import pytz

from datetime import datetime
from flask import g, request, jsonify, send_file, abort
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.db import session
from scoring_engine.models.team import Team
from scoring_engine.models.inject import Template, Inject, File, Comment

from . import make_cache_key, mod


@mod.route("/api/injects")
@login_required
def api_injects():
    team = session.get(Team, current_user.team.id)
    if team is None or not current_user.team == team or not (current_user.is_blue_team or current_user.is_red_team):
        return jsonify({"status": "Unauthorized"}), 403
    data = list()
    injects = (
        session.query(Inject)
        .options(joinedload(Inject.template))
        .join(Template)
        .filter(Inject.team == team)
        .filter(Inject.enabled == True)
        .filter(Template.start_time < datetime.utcnow())
        .all()
    )
    for inject in injects:
        data.append(
            dict(
                id=inject.id,
                template_id=inject.template.id,
                title=inject.template.title,
                score=inject.score,
                max_score=inject.template.score,
                status=inject.status,
                start_time=inject.template.start_time,
                end_time=inject.template.end_time,
            )
        )
    return jsonify(data=data)


@mod.route("/api/inject/<inject_id>/submit", methods=["POST"])
@login_required
def api_injects_submit(inject_id):
    inject = session.get(Inject, inject_id)
    if inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403
    if datetime.utcnow() > inject.template.end_time:
        return jsonify({"status": "Inject has ended"}), 403
    inject.status = "Submitted"
    inject.submitted = datetime.utcnow()
    session.commit()
    data = list()
    return jsonify(data=data)


@mod.route("/api/inject/<inject_id>/upload", methods=["POST"])
@login_required
def api_injects_file_upload(inject_id):
    inject = session.get(Inject, inject_id)
    if inject.team is None or not current_user.team == inject.team or not current_user.is_blue_team:
        return jsonify({"status": "Unauthorized"}), 403

    # Validate inject is still valid
    if datetime.utcnow() > inject.template.end_time:
        return "Inject has ended", 400
    # Validate inject isn't submitted yet
    if inject.status != "Draft":
        return "Inject was already submitted", 400
    # Validate file exists
    if not request.files:
        return jsonify({"status": "No file part"}), 400

    files = request.files.getlist("file")
    for file in files:
        filename = "Inject" + str(inject_id) + "_" + current_user.team.name + "_" + secure_filename(file.filename)
        path = os.path.join(config.upload_folder, inject_id, current_user.team.name)

        if not os.path.exists(path):
            os.makedirs(path)
        # Check if file exists already
        if session.query(File).filter(File.name == filename).one_or_none():
            return "File name is not unique", 400
        file.save(os.path.join(path, filename))

        f = File(filename, current_user, inject)
        session.add(f)
        session.commit()

        # Delete file cache for inject
        cache.delete(f"/api/inject/{inject_id}/files_{g.user.team.id}")

    return jsonify({"status": "Inject Submitted Successfully"}), 200


@mod.route("/api/inject/<inject_id>")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject(inject_id):
    inject = session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    data = {}

    data["score"] = inject.score
    data["status"] = inject.status

    # Comments
    comments = (
        session.query(Comment)
        .options(joinedload(Comment.user).joinedload("team"))
        .filter(Comment.inject == inject)
        .order_by(Comment.time)
        .all()
    )
    data["comments"] = [
        {
            "id": comment.id,
            "text": comment.get_full_comment(),  # Get full comment from file or DB
            "user": comment.user.username,
            "team": comment.user.team.name,
            "added": comment.time.astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "is_truncated": comment.is_stored_in_file,
        }
        for comment in comments
    ]

    # Files
    files = session.query(File.id, File.name).filter(File.inject_id == inject_id).order_by(File.name).all()
    data["files"] = [{"id": file[0], "name": file[1]} for file in files]

    return jsonify(data), 200


@mod.route("/api/inject/<inject_id>/comments")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject_comments(inject_id):
    inject = session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    data = []
    comments = (
        session.query(Comment)
        .options(joinedload(Comment.user).joinedload("team"))
        .filter(Comment.inject == inject)
        .order_by(Comment.time)
        .all()
    )
    for comment in comments:
        # Get full comment text (from file or database)
        comment_text = comment.get_full_comment()

        data.append(
            {
                "id": comment.id,
                "text": comment_text,
                "user": comment.user.username,
                "team": comment.user.team.name,
                "added": comment.time.astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z"),
                "is_truncated": comment.is_stored_in_file,  # Indicate if full text is in file
            }
        )

    return jsonify(data=data), 200


@mod.route("/api/inject/<inject_id>/comment", methods=["POST"])
@login_required
def api_inject_add_comment(inject_id):
    from scoring_engine.file_storage import (
        should_use_file_storage_for_comment,
        save_comment_to_file
    )

    inject = session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403
    if datetime.utcnow() > inject.template.end_time:
        return jsonify({"status": "Inject has ended"}), 400

    data = request.get_json()
    if "comment" not in data or data["comment"] == "":
        return jsonify({"status": "No comment"}), 400

    comment_text = data["comment"]

    # Decide whether to store in file or database
    if should_use_file_storage_for_comment(comment_text):
        # Create comment first to get ID
        c = Comment("", current_user, inject)  # Temporary empty comment
        session.add(c)
        session.flush()  # Get the ID without committing

        # Save to file and update comment
        file_path, preview = save_comment_to_file(
            c.id, inject.id, current_user.team.name, comment_text
        )
        c.comment = preview  # Store preview in DB
        c.file_path = file_path
        c.preview = preview
    else:
        # Store entirely in database (backward compatible)
        c = Comment(comment_text, current_user, inject)
        session.add(c)

    session.commit()

    # Delete comment cache for inject
    cache.delete(f"/api/inject/{inject_id}/comments_{g.user.team.id}")

    return jsonify({"status": "Comment added"}), 200


@mod.route("/api/inject/<inject_id>/files")
@cache.cached(make_cache_key=make_cache_key)
@login_required
def api_inject_files(inject_id):
    inject = session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    files = session.query(File.id, File.name).filter(File.inject_id == inject_id).order_by(File.name).all()

    if files is None:
        return jsonify({"status": "Unauthorized"}), 403

    data = []
    for file in files:
        data.append({"id": file[0], "name": file[1]})

    return jsonify(data=data)


@mod.route("/api/inject/<inject_id>/files/<file_id>/download")
@login_required
def api_inject_download(inject_id, file_id):
    inject = session.get(Inject, inject_id)
    if inject is None or not (current_user.team == inject.team or current_user.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    file = session.query(File).filter(File.id == file_id).one_or_none()

    if file is None:
        return jsonify({"status": "Unauthorized"}), 403

    path = os.path.join(config.upload_folder, inject_id, inject.team.name, file.name)
    try:
        return send_file(path, as_attachment=True)
    except FileNotFoundError:
        abort(404)
