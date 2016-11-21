from flask import Blueprint, flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_required
from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web.cache import cache
from sqlalchemy.orm.exc import NoResultFound
import json
import random


mod = Blueprint('api', __name__)


@mod.route('/api/admin/get_round_progress')
@login_required
def get_check_progress_total():
    if current_user.is_white_team:
        return json.dumps({'Total': random.randint(1, 100),
                           'Team1': random.randint(1, 100),
                           'Team2': random.randint(1, 100),
                           'Team3': random.randint(1, 100),
                           'Team4': random.randint(1, 100),
                           'Team5': random.randint(1, 100)})
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/get_teams')
@login_required
def admin_get_teams():
    if current_user.is_white_team:
        all_teams = Team.query.all()
        data = []
        for team in all_teams:
            users = {}
            for user in team.users:
                users[user.username] = [user.password, str(user.authenticated).title()]
            data.append({'name': team.name, 'color': team.color, 'users': users})
        return jsonify(data=data)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_password', methods=['POST'])
@login_required
def admin_update_password():
    if current_user.is_white_team:
        if 'user_id' in request.form and 'password' in request.form:
            try:
                user_obj = User.query.filter(User.id == request.form['user_id']).one()
            except NoResultFound:
                return redirect(url_for('auth.login'))
            user_obj.update_password(request.form['password'])
            user_obj.authenticated = False
            db.save(user_obj)
            flash('Password Successfully Updated.', 'success')
            return redirect(url_for('admin.manage'))
        else:
            flash('Error: user_id or password not specified.', 'danger')
            return redirect(url_for('admin.manage'))
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/add_user', methods=['POST'])
@login_required
def admin_add_user():
    if current_user.is_white_team:
        if 'username' in request.form and 'password' in request.form and 'team_id' in request.form:
            team_obj = Team.query.filter(Team.id == request.form['team_id']).one()
            user_obj = User(username=request.form['username'],
                            password=request.form['password'],
                            team=team_obj)
            db.save(user_obj)
            flash('User successfully added.', 'success')
            return redirect(url_for('admin.manage'))
        else:
            flash('Error: Username, Password, or Team ID not specified.', 'danger')
            return redirect(url_for('admin.manage'))
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/add_team', methods=['POST'])
@login_required
def admin_add_team():
    if current_user.is_white_team:
        if 'name' in request.form and 'color' in request.form:
            team_obj = Team(request.form['name'], request.form['color'])
            db.save(team_obj)
            flash('Team successfully added.', 'success')
            return redirect(url_for('admin.manage'))
        else:
            flash('Error: Team name or color not defined.', 'danger')
            return redirect(url_for('admin.manage'))
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/profile/update_password', methods=['POST'])
@login_required
def profile_update_password():
    if 'user_id' in request.form and 'password' in request.form:
        if str(current_user.id) == request.form['user_id']:
            current_user.update_password(request.form['password'])
            current_user.authenticated = False
            db.save(current_user)
            flash('Password Successfully Updated.', 'success')
            return redirect(url_for('profile.home'))
        else:
            return {'status': 'Unauthorized'}, 403
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/service/get_checks/<id>')
@login_required
def get_checks(id):
    service = Service.query.get(id)
    if service is None or not current_user.team == service.team:
        return jsonify({'status': 'Unauthorized'}), 403
    data = []
    for check in service.checks_reversed:
        data.append({'round': check.round.number,
                     'result': check.result,
                     'timestamp': check.completed_timestamp,
                     'output': check.output})
    return jsonify(data=data)


@cache.cached(timeout=30)
@mod.route('/api/scoreboard/get_bar_data')
def scoreboard_get_bar_data():
    results = Team.get_all_rounds_results()
    team_data = {}

    team_labels = []
    team_scores = []
    scores_colors = []
    for blue_team in Team.get_all_blue_teams():
        team_labels.append(blue_team.name)
        team_scores.append(blue_team.current_score)
        scores_colors.append(blue_team.rgb_color)

    team_data['labels'] = team_labels
    team_data['scores'] = team_scores
    team_data['colors'] = scores_colors

    return jsonify(team_data)


@mod.route('/api/scoreboard/get_line_data')
@cache.cached(timeout=30)
def scoreboard_get_line_data():
    results = Team.get_all_rounds_results()
    team_data = {}
    team_data['team'] = {}
    team_data['round'] = results['rounds']
    # We start at one because that's how javascript expects the team_data
    current_index = 1
    for name in sorted(results['scores'].keys()):
        scores = results['scores'][name]
        rgb_color = results['rgb_colors'][name]
        team_data['team'][current_index] = {
            "label": name,
            "data": scores,
            "color": rgb_color
        }
        current_index += 1

    return jsonify(team_data)
