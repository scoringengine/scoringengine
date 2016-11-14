from flask import Blueprint, render_template

overview_view = Blueprint('overview', __name__)


@overview_view.route('/overview')
def home():
    return render_template('overview.html')
