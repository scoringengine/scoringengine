import os
from flask import Blueprint, render_template, redirect, url_for

from scoring_engine.db import session
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from .setup import competition_file_path

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    comp_exists = os.path.exists(competition_file_path())
    teams_exist = session.query(Team).count() > 0
    if not comp_exists or not teams_exist:
        return redirect(url_for('setup.setup'))
    welcome_content = Setting.get_setting('welcome_page_content').value
    return render_template('welcome.html', welcome_content=welcome_content)
