from flask import Blueprint, render_template

mod = Blueprint('overview', __name__)

from scoring_engine.models import *


@mod.route('/overview')
def home():
    blue_teams = Team.query.filter(Team.color == 'Blue').all()
    services = blue_teams[0].services
    return render_template('overview.html', header_services=services, blue_teams=blue_teams)
