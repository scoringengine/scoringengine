from flask import Blueprint, render_template

mod = Blueprint('koth_overview', __name__)


@mod.route('/koth_overview')
def home():
    return render_template('koth-overview.html')
