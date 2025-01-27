from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from scoring_engine.models.team import Team

mod = Blueprint("flags", __name__)


@mod.route("/flags")
@login_required
def home():
    if not (current_user.is_red_team or current_user.is_white_team):
        return redirect(url_for("auth.unauthorized"))

    return render_template("flags.html", teams=Team.get_all_blue_teams())
