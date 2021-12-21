from flask import Blueprint, render_template

from scoring_engine.models.team import Team

mod = Blueprint("overview", __name__)


@mod.route("/overview")
def home():
    return render_template("overview.html", teams=Team.get_all_blue_teams())
