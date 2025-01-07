from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc
from sqlalchemy.sql import func

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.db import session

import pytz

mod = Blueprint("stats", __name__)


@mod.route("/stats")
@login_required
def home():
    if not (current_user.is_blue_team or current_user.is_white_team):
        return redirect(url_for("auth.unauthorized"))

    return render_template("stats.html")
