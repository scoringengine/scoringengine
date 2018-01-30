import json
import random

from collections import OrderedDict

from flask import Blueprint, flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_required

import html

from scoring_engine.db import session
from scoring_engine.models.account import Account
from scoring_engine.models.service import Service
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.setting import Setting
from scoring_engine.engine.execute_command import execute_command

from sqlalchemy.orm.exc import NoResultFound


mod = Blueprint('api', __name__)


@mod.route('/api/update_account_info', methods=['POST'])
@login_required
def update_service_account_info():
    if current_user.is_white_team or current_user.is_blue_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            account = session.query(Account).get(int(request.form['pk']))
            if current_user.team == account.service.team or current_user.is_white_team:
                if account:
                    if request.form['name'] == 'username':
                        account.username = html.escape(request.form['value'])
                    elif request.form['name'] == 'password':
                        account.password = html.escape(request.form['value'])
                    session.add(account)
                    session.commit()
                    return jsonify({'status': 'Updated Account Information'})
                return jsonify({'error': 'Incorrect permissions'})
            return jsonify({'error': 'Incorrect permissions'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_environment_info', methods=['POST'])
@login_required
def admin_update_environment():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            environment = session.query(Environment).get(int(request.form['pk']))
            if environment:
                if request.form['name'] == 'matching_regex':
                    environment.matching_regex = html.escape(request.form['value'])
                session.add(environment)
                session.commit()
                return jsonify({'status': 'Updated Environment Information'})
            return jsonify({'error': 'Incorrect permissions'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_property', methods=['POST'])
@login_required
def admin_update_property():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            property_obj = session.query(Property).get(int(request.form['pk']))
            if property_obj:
                if request.form['name'] == 'property_name':
                    property_obj.name = html.escape(request.form['value'])
                elif request.form['name'] == 'property_value':
                    property_obj.value = html.escape(request.form['value'])
                session.add(property_obj)
                session.commit()
                return jsonify({'status': 'Updated Property Information'})
            return jsonify({'error': 'Incorrect permissions'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_check', methods=['POST'])
@login_required
def admin_update_check():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            check = session.query(Check).get(int(request.form['pk']))
            if check:
                if request.form['name'] == 'check_value':
                    if request.form['value'] == '1':
                        check.result = True
                    elif request.form['value'] == '2':
                        check.result = False
                    session.add(check)
                    session.commit()
                    return jsonify({'status': 'Updated Property Information'})
            return jsonify({'error': 'Incorrect permissions'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_host', methods=['POST'])
@login_required
def admin_update_host():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if request.form['name'] == 'host':
                    service.host = html.escape(request.form['value'])
                    session.add(service)
                    session.commit()
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_port', methods=['POST'])
@login_required
def admin_update_port():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if request.form['name'] == 'port':
                    service.port = int(request.form['value'])
                    session.add(service)
                    session.commit()
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/update_host', methods=['POST'])
@login_required
def update_host():
    if current_user.is_blue_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if service.team == current_user.team and request.form['name'] == 'host':
                    service.host = html.escape(request.form['value'])
                    session.add(service)
                    session.commit()
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_about_page_content', methods=['POST'])
@login_required
def admin_update_about_page_content():
    if current_user.is_white_team:
        if 'about_page_content' in request.form:
            setting = Setting.get_setting('about_page_content')
            setting.value = request.form['about_page_content']
            session.add(setting)
            session.commit()
            flash('About Page Content Successfully Updated.', 'success')
            return redirect(url_for('admin.settings'))
        flash('Error: about_page_content not specified.', 'danger')
        return redirect(url_for('admin.manage'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_welcome_page_content', methods=['POST'])
@login_required
def admin_update_welcome_page_content():
    if current_user.is_white_team:
        if 'welcome_page_content' in request.form:
            setting = Setting.get_setting('welcome_page_content')
            setting.value = request.form['welcome_page_content']
            session.add(setting)
            session.commit()
            flash('Welcome Page Content Successfully Updated.', 'success')
            return redirect(url_for('admin.settings'))
        flash('Error: welcome_page_content not specified.', 'danger')
        return redirect(url_for('admin.manage'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_round_time_sleep', methods=['POST'])
@login_required
def admin_update_round_time_sleep():
    if current_user.is_white_team:
        if 'round_time_sleep' in request.form:
            setting = Setting.get_setting('round_time_sleep')
            input_time = request.form['round_time_sleep']
            if not input_time.isdigit():
                flash('Error: Round Sleep Time must be an integer.', 'danger')
                return redirect(url_for('admin.settings'))
            setting.value = input_time
            session.add(setting)
            session.commit()
            flash('Round Sleep Time Successfully Updated.', 'success')
            return redirect(url_for('admin.settings'))
        flash('Error: round_time_sleep not specified.', 'danger')
        return redirect(url_for('admin.settings'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_worker_refresh_time', methods=['POST'])
@login_required
def admin_update_worker_refresh_time():
    if current_user.is_white_team:
        if 'worker_refresh_time' in request.form:
            setting = Setting.get_setting('worker_refresh_time')
            input_time = request.form['worker_refresh_time']
            if not input_time.isdigit():
                flash('Error: Worker Refresh Time must be an integer.', 'danger')
                return redirect(url_for('admin.settings'))
            setting.value = input_time
            session.add(setting)
            session.commit()
            flash('Worker Refresh Time Successfully Updated.', 'success')
            return redirect(url_for('admin.settings'))
        flash('Error: worker_refresh_time not specified.', 'danger')
        return redirect(url_for('admin.settings'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/modify_service_account', methods=['POST'])
@login_required
def modify_service_account():
    if current_user.is_blue_team:
        if 'account_id' in request.form and 'password' in request.form:
            account = session.query(Account).get(int(request.form['account_id']))
            if account:
                if account.service.team == current_user.team:
                    account.password = html.escape(request.form['password'])
                    session.add(account)
                    session.commit()
                    flash('Successfully updated password for ' + account.username, 'success')
                    return redirect('/service/' + str(account.service.id))
            flash('Incorrect permissions', 'error')
            return jsonify({'error': 'Incorrect permissions'})
    flash('Incorrect permissions', 'error')
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/get_round_progress')
@login_required
def get_check_progress_total():
    if current_user.is_white_team:
        task_id_settings = session.query(KB).filter_by(name='task_ids').order_by(KB.round_num.desc()).first()
        total_stats = {}
        total_stats['finished'] = 0
        total_stats['pending'] = 0

        team_stats = {}
        if task_id_settings:
            task_dict = json.loads(task_id_settings.value)
            for team_name, task_ids in task_dict.items():
                for task_id in task_ids:
                    task = execute_command.AsyncResult(task_id)
                    if team_name not in team_stats:
                        team_stats[team_name] = {}
                        team_stats[team_name]['pending'] = 0
                        team_stats[team_name]['finished'] = 0

                    if task.state == 'PENDING':
                        team_stats[team_name]['pending'] += 1
                        total_stats['pending'] += 1
                    else:
                        team_stats[team_name]['finished'] += 1
                        total_stats['finished'] += 1

        total_percentage = 0
        total_tasks = total_stats['finished'] + total_stats['pending']
        if total_stats['finished'] == 0:
            total_percentage = 0
        elif total_tasks == 0:
            total_percentage = 100
        elif total_stats and total_stats['finished']:
            total_percentage = int((total_stats['finished'] / total_tasks) * 100)

        output_dict = {'Total': total_percentage}
        for team_name, team_stat in team_stats.items():
            team_total_percentage = 0
            team_total_tasks = team_stat['finished'] + team_stat['pending']
            if team_stat['finished'] == 0:
                team_total_percentage = 0
            elif team_total_tasks == 0:
                team_total_percentage = 100
            elif team_stat and team_stat['finished']:
                team_total_percentage = int((team_stat['finished'] / team_total_tasks) * 100)
            output_dict[team_name] = team_total_percentage

        return json.dumps(output_dict)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/get_teams')
@login_required
def admin_get_teams():
    if current_user.is_white_team:
        all_teams = session.query(Team).all()
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
                user_obj = session.query(User).filter(User.id == request.form['user_id']).one()
            except NoResultFound:
                return redirect(url_for('auth.login'))
            user_obj.update_password(html.escape(request.form['password']))
            user_obj.authenticated = False
            session.add(user_obj)
            session.commit()
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
            team_obj = session.query(Team).filter(Team.id == request.form['team_id']).one()
            user_obj = User(username=html.escape(request.form['username']),
                            password=html.escape(request.form['password']),
                            team=team_obj)
            session.add(user_obj)
            session.commit()
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
            team_obj = Team(html.escape(request.form['name']), html.escape(request.form['color']))
            session.add(team_obj)
            session.commit()
            flash('Team successfully added.', 'success')
            return redirect(url_for('admin.manage'))
        else:
            flash('Error: Team name or color not defined.', 'danger')
            return redirect(url_for('admin.manage'))
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/get_engine_stats')
@login_required
def admin_get_engine_stats():
    if current_user.is_white_team:
        engine_stats = {}
        engine_stats['round_number'] = Round.get_last_round_num()
        engine_stats['num_passed_checks'] = session.query(Check).filter_by(result=True).count()
        engine_stats['num_failed_checks'] = session.query(Check).filter_by(result=False).count()
        engine_stats['total_checks'] = session.query(Check).count()
        return jsonify(engine_stats)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/overview/get_data')
def overview_get_data():
    blue_teams = session.query(Team).filter(Team.color == 'Blue').all()
    columns = []
    columns.append('Team Name')
    columns.append('Current Score')
    for service in blue_teams[0].services:
        columns.append(service.name)
    data = []
    for team in blue_teams:
        count = 0
        team_dict = {}
        for x in range(0, len(columns)):
            if columns[x] == "Team Name":
                team_dict[columns[x]] = team.name
                count += 1
            elif columns[x] == "Current Score":
                team_dict[columns[x]] = team.current_score
                count += 1
            else:
                service = session.query(Service).filter(Service.name == columns[x]).filter(Service.team == team).first()
                service_text = service.host
                if str(service.port) != '0':
                    service_text += ':' + str(service.port)
                service_text += ' - ' + str(service.last_check_result())
                team_dict[columns[x]] = service_text
        data.append(team_dict)
    columnlist = []
    for column in columns:
        columnlist.append({'title': column, 'data': column})
    return jsonify(columns=columnlist, data=data)


@mod.route('/api/overview/get_round_data')
def overview_get_round_data():
    round_obj = session.query(Round).order_by(Round.number.desc()).first()
    if round_obj:
        round_start = round_obj.local_round_start
        number = round_obj.number
    else:
        round_start = ""
        number = 0
    data = {'round_start': round_start, 'number': number}
    return jsonify(data)


@mod.route('/api/services/get_team_data')
@login_required
def services_get_team_data():
    if current_user.is_blue_team:
        current_team = current_user.team
        data = {
            'place': current_team.place,
            'current_score': current_team.current_score
        }
        return jsonify(data)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/profile/update_password', methods=['POST'])
@login_required
def profile_update_password():
    if 'user_id' in request.form and 'password' in request.form:
        if str(current_user.id) == request.form['user_id']:
            current_user.update_password(html.escape(request.form['password']))
            current_user.authenticated = False
            session.add(current_user)
            session.commit()
            flash('Password Successfully Updated.', 'success')
            return redirect(url_for('profile.home'))
        else:
            return {'status': 'Unauthorized'}, 403
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/services')
@login_required
def api_services():
    team = current_user.team
    if not current_user.is_blue_team:
        return jsonify({'status': 'unauthorized'})
    data = []
    for service in team.services:
        if not service.checks:
            check = 'Undetermined'
        else:
            if service.last_check_result():
                check = 'UP'
            else:
                check = 'DOWN'
        data.append(dict(
            service_id=service.id,
            service_name=service.name,
            host=service.host,
            port=service.port,
            check=check,
            rank=service.rank,
            score_earned=service.score_earned,
            max_score=service.max_score,
            percent_earned=service.percent_earned,
            pts_per_check=service.points,
            last_ten_checks=[check.result for check in service.last_ten_checks[::-1]]
        ))
    return jsonify(data=data)


@mod.route('/api/service/get_checks/<id>')
@login_required
def service_get_checks(id):
    service = session.query(Service).get(id)
    if service is None or not current_user.team == service.team:
        return jsonify({'status': 'Unauthorized'}), 403
    data = []
    for check in service.checks_reversed:
        data.append({
            'round': check.round.number,
            'result': check.result,
            'timestamp': check.local_completed_timestamp,
            'reason': check.reason,
            'output': check.output,
        })
    return jsonify(data=data)


@mod.route('/api/scoreboard/get_bar_data')
def scoreboard_get_bar_data():
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
def scoreboard_get_line_data():
    results = Team.get_all_rounds_results()
    team_data = {'team': {}, 'round': results['rounds']}
    # We start at one because that's how javascript expects the team_data
    current_index = 1
    for name in results['scores'].keys():
        scores = results['scores'][name]
        rgb_color = results['rgb_colors'][name]
        team_data['team'][current_index] = {
            "label": name,
            "data": scores,
            "color": rgb_color
        }
        current_index += 1
    return jsonify(team_data)


@mod.route('/api/overview/data')
def overview_data():
    team_data = OrderedDict()
    teams = session.query(Team).filter(Team.color == 'Blue').order_by(Team.id).all()
    random.shuffle(teams)
    for team in teams:
        service_data = {}
        for service in team.services:
            service_data[service.name] = {
                'passing': service.last_check_result(),
                'host': service.host,
                'port': service.port,
            }
        team_data[team.name] = service_data
    return json.dumps(team_data)
