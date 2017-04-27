from flask import Blueprint, render_template
from scoring_engine.version import version
from scoring_engine.engine.config import config

mod = Blueprint('about', __name__)


@mod.route('/about')
def about():
    return render_template('about.html', version=version, config_about_content=config.web_about_us_page_content)
