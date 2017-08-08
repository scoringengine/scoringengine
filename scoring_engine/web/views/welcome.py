from flask import Blueprint, render_template

from scoring_engine.models.setting import Setting

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    welcome_content = Setting.get_setting('welcome_page_content').value
    return render_template('welcome.html', welcome_content=welcome_content)
