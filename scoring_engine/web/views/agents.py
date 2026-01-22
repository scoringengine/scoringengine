from flask import Blueprint, render_template, redirect, url_for

from scoring_engine.models.team import Team
from scoring_engine.models.setting import Setting

mod = Blueprint("agents", __name__)


@mod.route("/agents")
def home():
    # Check if BTA is enabled
    psk_setting = Setting.get_setting("agent_psk")
    if not psk_setting or not psk_setting.value:
        return redirect(url_for("welcome.home"))

    return render_template("agents.html", teams=Team.get_all_blue_teams())
