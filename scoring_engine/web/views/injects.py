from datetime import datetime, timezone
from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user
from scoring_engine.models.inject import Inject, File
from scoring_engine.db import db


mod = Blueprint("injects", __name__)


@mod.route("/injects")
@login_required
def home():
    if not (current_user.is_blue_team or current_user.is_red_team):
        return redirect(url_for("auth.unauthorized"))
    return render_template(
        "injects.html"
    )


@mod.route("/inject/<inject_id>")
@login_required
def inject(inject_id):
    inject = db.session.get(Inject, inject_id)
    now = datetime.now(timezone.utc)
    start_time = inject.template.start_time if inject else None
    # Handle naive datetimes from databases that don't support timezones
    if start_time is not None and start_time.tzinfo is None:
        now = now.replace(tzinfo=None)
    if (
        inject is None
        or not current_user.team == inject.team
        or now < start_time
    ):
        return redirect(url_for("auth.unauthorized"))

    files = (
        db.session.query(File)
        .filter(File.inject_id == inject_id)
        .order_by(File.name)
        .all()
    )

    return render_template(
        "inject.html",
        inject=inject,
        files=files,
    )
