from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import login_required, current_user
from scoring_engine.db import db

mod = Blueprint('profile', __name__)


@mod.route('/profile')
@login_required
def home():
    return render_template('profile.html')


@mod.route('/profile/api/update_password', methods=['POST'])
@login_required
def update_password():
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
