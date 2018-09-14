from flask import Blueprint, render_template

from scoring_engine.models.setting import Setting

mod = Blueprint('overview', __name__)


@mod.route('/overview')
def home():
    return render_template(
      'overview.html',
      overview_show_round_info=Setting.get_setting('overview_show_round_info').value
    )
