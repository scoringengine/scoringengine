from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from operator import itemgetter

from scoring_engine.models.user import User
from scoring_engine.models.team import Team
from scoring_engine.models.inject import Inject
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.db import db


mod = Blueprint("admin", __name__)


@mod.route("/admin")
@mod.route("/admin/status")
@login_required
def status():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template("admin/status.html", blue_teams=blue_teams)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/workers")
@login_required
def workers():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template("admin/workers.html", blue_teams=blue_teams)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/queues")
@login_required
def queues():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template("admin/queues.html", blue_teams=blue_teams)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/manage")
@login_required
def manage():
    if current_user.is_white_team:
        users = db.session.query(User).with_entities(User.id, User.username).all()
        teams = db.session.query(Team).with_entities(Team.id, Team.name).all()
        blue_teams = Team.get_all_blue_teams()
        return render_template(
            "admin/manage.html",
            users=sorted(users, key=itemgetter(0)),
            teams=teams,
            blue_teams=blue_teams,
        )
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/injects/templates")
@login_required
def inject_templates():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        red_teams = Team.get_all_red_teams()
        return render_template(
            "admin/templates.html", blue_teams=blue_teams, red_teams=red_teams
        )
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/injects/scores")
@login_required
def inject_scores():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template("admin/injects.html", blue_teams=blue_teams)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/injects/<int:inject_id>")
@login_required
def inject_inject(inject_id):
    if current_user.is_white_team:
        inject = db.session.get(Inject, inject_id)
        return render_template("admin/inject.html", inject=inject)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/service/<id>")
@login_required
def service(id):
    if current_user.is_white_team:
        service = db.session.get(Service, id)
        blue_teams = Team.get_all_blue_teams()
        if service is None:
            return redirect(url_for("auth.unauthorized"))

        return render_template(
            "admin/service.html", service=service, blue_teams=blue_teams
        )
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/settings")
@login_required
def settings():
    if current_user.is_white_team:
        about_page_content = Setting.get_setting("about_page_content").value
        welcome_page_content = Setting.get_setting("welcome_page_content").value
        target_round_time = Setting.get_setting("target_round_time").value
        worker_refresh_time = Setting.get_setting("worker_refresh_time").value
        blue_teams = Team.get_all_blue_teams()
        return render_template(
            "admin/settings.html",
            blue_teams=blue_teams,
            target_round_time=target_round_time,
            worker_refresh_time=worker_refresh_time,
            about_page_content=about_page_content,
            welcome_page_content=welcome_page_content,
        )
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/permissions")
@login_required
def permissions():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template(
            "admin/permissions.html",
            blue_teams=blue_teams,
            blue_team_update_hostname=Setting.get_setting(
                "blue_team_update_hostname"
            ).value,
            blue_team_update_port=Setting.get_setting("blue_team_update_port").value,
            blue_team_update_account_usernames=Setting.get_setting(
                "blue_team_update_account_usernames"
            ).value,
            blue_team_update_account_passwords=Setting.get_setting(
                "blue_team_update_account_passwords"
            ).value,
            blue_team_view_check_output=Setting.get_setting(
                "blue_team_view_check_output"
            ).value,
            blue_team_view_status_page=Setting.get_setting(
                "blue_team_view_status_page"
            ).value,
        )
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/sla")
@login_required
def sla():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()

        # Get SLA settings with defaults
        def get_setting_value(name, default):
            setting = Setting.get_setting(name)
            return setting.value if setting else default

        def get_setting_bool(name, default):
            setting = Setting.get_setting(name)
            if setting:
                val = setting.value
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ("true", "1", "yes")
            return default

        return render_template(
            "admin/sla.html",
            blue_teams=blue_teams,
            # SLA Penalty settings
            sla_enabled=get_setting_bool("sla_enabled", False),
            sla_penalty_threshold=get_setting_value("sla_penalty_threshold", "5"),
            sla_penalty_percent=get_setting_value("sla_penalty_percent", "10"),
            sla_penalty_max_percent=get_setting_value("sla_penalty_max_percent", "50"),
            sla_penalty_mode=get_setting_value("sla_penalty_mode", "additive"),
            sla_allow_negative=get_setting_bool("sla_allow_negative", False),
            # Dynamic scoring settings
            dynamic_scoring_enabled=get_setting_bool("dynamic_scoring_enabled", False),
            dynamic_scoring_early_rounds=get_setting_value("dynamic_scoring_early_rounds", "10"),
            dynamic_scoring_early_multiplier=get_setting_value("dynamic_scoring_early_multiplier", "2.0"),
            dynamic_scoring_late_start_round=get_setting_value("dynamic_scoring_late_start_round", "50"),
            dynamic_scoring_late_multiplier=get_setting_value("dynamic_scoring_late_multiplier", "0.5"),
        )
    else:
        return redirect(url_for("auth.unauthorized"))
