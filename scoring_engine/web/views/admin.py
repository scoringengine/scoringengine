from flask import Blueprint, render_template, request
from flask_login import login_required
from scoring_engine.models import User
from scoring_engine.db import db
import json


mod = Blueprint('admin', __name__)


@mod.route('/admin')
@mod.route('/admin/status')
@login_required
def status():
    return render_template('admin/status.html')


@mod.route('/admin/manage')
@login_required
def manage():
    res = User.query(User.id, User.username)
    for row in res: print(res.__dict__)
    return render_template('admin/manage.html')


@mod.route('/admin/stats')
@login_required
def stats():
    return render_template('admin/stats.html')


@mod.route('/admin/api/get_progress/total')
@login_required
def get_progress_total():
    import json
    import random
    return json.dumps({'Total': random.randint(1, 100),
                       'Team1': random.randint(1, 100),
                       'Team2': random.randint(1, 100),
                       'Team3': random.randint(1, 100),
                       'Team4': random.randint(1, 100),
                       'Team5': random.randint(1, 100)})


@mod.route('/admin/api/update_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_password(user_id):
    #password = request.form
    #print(password)
    password = "password"
    user_obj = User.query.filter(User.id == user_id).one()
    user_obj.update_password(password)
    db.session.commit()
    return json.dumps({'success': True}), 200, {'Content-Type': 'application/json'}
