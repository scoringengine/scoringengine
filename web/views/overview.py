from flask import Blueprint, render_template

overview_blueprint = Blueprint('overview', __name__)


@overview_blueprint.route('/overview')
def home():
    return render_template('overview.html')
