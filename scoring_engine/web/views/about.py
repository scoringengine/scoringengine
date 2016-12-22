from flask import Blueprint, render_template
from scoring_engine import __version__

mod = Blueprint('about', __name__)


@mod.route('/about')
def about():
    return render_template('about.html', version=__version__)
