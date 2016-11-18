from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required
from operator import itemgetter
from scoring_engine.db import db
from scoring_engine.models.user import User
from scoring_engine.models.team import Team
import json
import random


mod = Blueprint('admin', __name__)


@mod.route('/admin')
@mod.route('/admin/status')
@login_required
def status():
    if current_user.is_white_team:
        return render_template('admin/status.html')
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/manage')
@login_required
def manage():
    if current_user.is_white_team:
        users = User.query.with_entities(User.id, User.username).all()
        teams = Team.query.with_entities(Team.id, Team.name).all()
        return render_template('admin/manage.html', users=sorted(users, key=itemgetter(0)), teams=teams)
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/stats')
@login_required
def stats():
    if current_user.is_white_team:
        return render_template('admin/stats.html')
    else:
        return redirect(url_for('auth.unauthorized'))


@mod.route('/admin/api/get_progress/total')
@login_required
def get_progress_total():
    if current_user.is_white_team:
        return json.dumps({'Total': random.randint(1, 100),
                           'Team1': random.randint(1, 100),
                           'Team2': random.randint(1, 100),
                           'Team3': random.randint(1, 100),
                           'Team4': random.randint(1, 100),
                           'Team5': random.randint(1, 100)})
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/admin/api/get_teams/all')
@login_required
def get_test_table_total():
    if current_user.is_white_team:
        all_teams = Team.query.all()
        data = []
        for team in all_teams:
            users = {}
            for user in team.users:
                users[user.username] = user.password
            data.append({'name': team.name, 'color': team.color, 'users': users})
        return jsonify(data=data)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/admin/api/update_password', methods=['POST'])
@login_required
def update_password():
    if current_user.is_white_team:
        if 'user_id' in request.form and 'password' in request.form:
            user_obj = User.query.filter(User.id == request.form['user_id']).one()
            user_obj.update_password(request.form['password'])
            db.save(user_obj)
            flash('Password Successfully Updated.', 'success')
            return redirect(url_for('admin.manage'))
        else:
            flash('Error: user_id or password not specified.', 'danger')
            return redirect(url_for('admin.manage'))
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/admin/api/add_user', methods=['POST'])
@login_required
def add_user():
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


@mod.route('/admin/api/add_team', methods=['POST'])
@login_required
def add_team():
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
