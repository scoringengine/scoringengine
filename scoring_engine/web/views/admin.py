from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from operator import itemgetter

from scoring_engine.models.user import User
from scoring_engine.models.team import Team
from scoring_engine.models.inject import Inject
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.db import session


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
        users = session.query(User).with_entities(User.id, User.username).all()
        teams = session.query(Team).with_entities(Team.id, Team.name).all()
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
        inject = session.query(Inject).get(inject_id)
        return render_template("admin/inject.html", inject=inject)
    else:
        return redirect(url_for("auth.unauthorized"))


@mod.route("/admin/service/<id>")
@login_required
def service(id):
    if current_user.is_white_team:
        service = session.query(Service).get(id)
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
        )
    else:
        return redirect(url_for("auth.unauthorized"))
