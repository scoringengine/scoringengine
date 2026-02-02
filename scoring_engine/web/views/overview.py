from flask import Blueprint, render_template
from flask_login import current_user

from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team

mod = Blueprint("overview", __name__)


def get_anonymize_mode():
    """
    Determine how team names should be displayed.
    Returns: (anonymize, show_both) tuple
    """
    setting = Setting.get_setting("anonymize_team_names")
    anonymize_enabled = setting.value is True if setting else False

    if not anonymize_enabled:
        return (False, False)

    if current_user.is_authenticated and current_user.is_white_team:
        return (False, True)

    return (True, False)


@mod.route("/overview")
def home():
    teams = Team.get_all_blue_teams()
    anonymize, show_both = get_anonymize_mode()

    team_name_map = Team.get_team_name_mapping(anonymize=anonymize, show_both=show_both)
    team_display = [{"name": team_name_map.get(t.id, t.name)} for t in teams]

    return render_template("overview.html", teams=team_display)
