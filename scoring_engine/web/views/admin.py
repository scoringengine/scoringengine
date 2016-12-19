from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from operator import itemgetter

from redis.exceptions import ConnectionError
import multiprocessing

from scoring_engine.models.user import User
from scoring_engine.models.team import Team
from scoring_engine.models.round import Round
from scoring_engine.models.check import Check
from scoring_engine.engine.worker_queue import WorkerQueue
from scoring_engine.engine.finished_queue import FinishedQueue


mod = Blueprint('admin', __name__)


def num_worker_queue():
    queue = WorkerQueue()
    return queue.size()


def num_finished_queue():
    queue = FinishedQueue()
    return queue.size()


@mod.route('/admin')
@mod.route('/admin/status')
@login_required
def status():
    if current_user.is_white_team:
        blue_teams = Team.get_all_blue_teams()
        engine_stats = {}
        engine_stats['num_worker_queue'] = 0
        engine_stats['num_finished_queue'] = 0

        try:
            p = multiprocessing.Process(target=num_worker_queue)
            p.start()
            p.join(2)
            if p.is_alive():
                engine_stats['num_worker_queue'] = 'Connection Timed Out'
                p.terminate()
                p.join()
        except ConnectionError:
            engine_stats['num_worker_queue'] = 'Connection Error'

        try:
            p = multiprocessing.Process(target=num_finished_queue)
            p.start()
            p.join(2)
            if p.is_alive():
                engine_stats['num_finished_queue'] = 'Connection Timed Out'
                p.terminate()
                p.join()
        except ConnectionError:
            engine_stats['num_finished_queue'] = 'Connection Error'

        engine_stats['round_number'] = Round.get_last_round_num() + 1
        engine_stats['num_passed_checks'] = Check.query.filter(Check.result is True).count()
        engine_stats['num_failed_checks'] = Check.query.filter(Check.result is False).count()
        engine_stats['total_checks'] = Check.query.count()

        return render_template('admin/status.html', engine_stats=engine_stats, blue_teams=blue_teams)
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


@mod.route('/admin/team/<id>')
@login_required
def team(id):
    if current_user.is_white_team:
        team = Team.query.get(id)
        if team is None:
            return redirect(url_for('auth.unauthorized'))

        return render_template('admin/team.html', team=team)
    else:
        return redirect(url_for('auth.unauthorized'))
