import json

from flask import flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_required

import html

from scoring_engine.db import session
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
from scoring_engine.cache_helper import update_scoreboard_data, update_overview_data, update_services_navbar, update_service_data, update_team_stats, update_services_data
from scoring_engine.celery_stats import CeleryStats

from sqlalchemy.orm.exc import NoResultFound

from . import mod


@mod.route('/api/admin/update_environment_info', methods=['POST'])
@login_required
def admin_update_environment():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            environment = session.query(Environment).get(int(request.form['pk']))
            if environment:
                if request.form['name'] == 'matching_content':
                    environment.matching_content = html.escape(request.form['value'])
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
                modified_check = False
                if request.form['name'] == 'check_value':
                    if request.form['value'] == '1':
                        check.result = True
                    elif request.form['value'] == '2':
                        check.result = False
                    modified_check = True
                elif request.form['name'] == 'check_reason':
                    modified_check = True
                    check.reason = request.form['value']
                if modified_check:
                    session.add(check)
                    session.commit()
                    update_scoreboard_data()
                    update_overview_data()
                    update_services_navbar(check.service.team.id)
                    update_team_stats(check.service.team.id)
                    update_services_data(check.service.team.id)
                    update_service_data(check.service.id)
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
                    update_overview_data()
                    update_services_data(service.team.id)
                    update_service_data(service.id)
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
                    update_overview_data()
                    update_services_data(service.team.id)
                    update_service_data(service.id)
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_worker_queue', methods=['POST'])
@login_required
def admin_update_worker_queue():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if request.form['name'] == 'worker_queue':
                    service.worker_queue = request.form['value']
                    session.add(service)
                    session.commit()
                    return jsonify({'status': 'Updated Service Information'})
    return jsonify({'error': 'Incorrect permissions'})


@mod.route('/api/admin/update_points', methods=['POST'])
@login_required
def admin_update_points():
    if current_user.is_white_team:
        if 'name' in request.form and 'value' in request.form and 'pk' in request.form:
            service = session.query(Service).get(int(request.form['pk']))
            if service:
                if request.form['name'] == 'points':
                    service.points = int(request.form['value'])
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


@mod.route('/api/admin/update_blueteam_edit_hostname', methods=['POST'])
@login_required
def admin_update_blueteam_edit_hostname():
    if current_user.is_white_team:
        setting = Setting.get_setting('blue_team_update_hostname')
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for('admin.permissions'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_blueteam_edit_port', methods=['POST'])
@login_required
def admin_update_blueteam_edit_port():
    if current_user.is_white_team:
        setting = Setting.get_setting('blue_team_update_port')
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for('admin.permissions'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_blueteam_edit_account_usernames', methods=['POST'])
@login_required
def admin_update_blueteam_edit_account_usernames():
    if current_user.is_white_team:
        setting = Setting.get_setting('blue_team_update_account_usernames')
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for('admin.permissions'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_blueteam_edit_account_passwords', methods=['POST'])
@login_required
def admin_update_blueteam_edit_account_passwords():
    if current_user.is_white_team:
        setting = Setting.get_setting('blue_team_update_account_passwords')
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for('admin.permissions'))
    return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/update_blueteam_view_check_output', methods=['POST'])
@login_required
def admin_update_blueteam_view_check_output():
    if current_user.is_white_team:
        setting = Setting.get_setting('blue_team_view_check_output')
        print(setting.__dict__)
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for('admin.permissions'))
    return {'status': 'Unauthorized'}, 403


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


@mod.route('/api/admin/get_worker_stats')
@login_required
def admin_get_worker_stats():
    if current_user.is_white_team:
        worker_stats = CeleryStats.get_worker_stats()
        return jsonify(data=worker_stats)
    else:
        return {'status': 'Unauthorized'}, 403


@mod.route('/api/admin/get_queue_stats')
@login_required
def admin_get_queue_stats():
    if current_user.is_white_team:
        queue_stats = CeleryStats.get_queue_stats()
        return jsonify(data=queue_stats)
    else:
        return {'status': 'Unauthorized'}, 403
