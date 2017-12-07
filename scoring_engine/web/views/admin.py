from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from operator import itemgetter

from scoring_engine.models.user import User
from scoring_engine.models.team import Team
from scoring_engine.models.setting import Setting
from scoring_engine.db import session


mod = Blueprint('admin', __name__)


@mod.route('/admin')
@mod.route('/admin/status')
@login_required
def status():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        return render_template('admin/status.html', blue_teams=blue_teams)
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/progress')
@login_required
def progress():
    if current_user.is_white_team:
        teams = session.query(Team).with_entities(Team.id, Team.name).all()
        blue_teams = Team.get_all_blue_teams()
        return render_template('admin/progress.html', teams=teams, blue_teams=blue_teams)
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/manage')
@login_required
def manage():
    if current_user.is_white_team:
        users = session.query(User).with_entities(User.id, User.username).all()
        teams = session.query(Team).with_entities(Team.id, Team.name).all()
        blue_teams = Team.get_all_blue_teams()
        return render_template('admin/manage.html', users=sorted(users, key=itemgetter(0)), teams=teams, blue_teams=blue_teams)
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/team/<id>')
@login_required
def team(id):
    if current_user.is_white_team:
        team = session.query(Team).get(id)
        blue_teams = Team.get_all_blue_teams()
        if team is None:
            return redirect(url_for('auth.unauthorized'))

        return render_template('admin/team.html', team=team, blue_teams=blue_teams)
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/settings')
@login_required
def settings():
    if current_user.is_white_team:
        about_page_content = Setting.get_setting('about_page_content').value
        welcome_page_content = Setting.get_setting('welcome_page_content').value
        blue_teams = Team.get_all_blue_teams()
        return render_template(
            'admin/settings.html',
            blue_teams=blue_teams,
            about_page_content=about_page_content,
            welcome_page_content=welcome_page_content
        )
    else:
        return redirect(url_for('auth.unauthorized'))
