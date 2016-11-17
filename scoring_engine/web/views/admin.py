from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from operator import itemgetter
from scoring_engine.db import db
from scoring_engine.models.user import User
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
    res = User.query.with_entities(User.id, User.username).all()
    return render_template('admin/manage.html', users=sorted(res, key=itemgetter(0)))


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


@mod.route('/admin/api/update_password', methods=['POST'])
@login_required
def update_password():
    print(request.form)
    if 'user_id' in request.form and 'password' in request.form:
        user_obj = User.query.filter(User.id == request.form['user_id']).one()
        user_obj.update_password(request.form['password'])
        db.session.commit()
        flash('Password Successfully Updated.', 'success')
        return redirect(url_for('admin.manage'))
    else:
        flash('Error: user_id or password not specified.', 'danger')
        return redirect(url_for('admin.manage'))
