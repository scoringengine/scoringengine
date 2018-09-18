from flask import Blueprint, render_template

from scoring_engine.models.setting import Setting

mod = Blueprint('overview', __name__)


@mod.route('/overview')
def home():
    show_round_info_setting = Setting.get_setting('overview_show_round_info')
    return render_template(
        'overview.html',
        overview_show_round_info=show_round_info_setting.value
    )
