from datetime import datetime
from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user
from scoring_engine.models.inject import Inject, File
from scoring_engine.db import session


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
    inject = session.query(Inject).get(inject_id)
    if (
        inject is None
        or not current_user.team == inject.team
        or datetime.utcnow() < inject.template.start_time
    ):
        return redirect(url_for("auth.unauthorized"))

    files = (
        session.query(File)
        .filter(File.inject_id == inject_id)
        .order_by(File.name)
        .all()
    )

    return render_template(
        "inject.html",
        inject=inject,
        files=files,
    )
