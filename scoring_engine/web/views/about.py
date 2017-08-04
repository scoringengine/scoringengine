from flask import Blueprint, render_template
from scoring_engine.version import version
from scoring_engine.models.setting import Setting

mod = Blueprint('about', __name__)


@mod.route('/about')
def about():
    about_content = Setting.get_setting('about_page_content').value
    return render_template('about.html', version=version, about_content=about_content)
