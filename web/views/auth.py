from flask import Blueprint, render_template

import bcrypt
from flask import flash, g, redirect, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf import FlaskForm

from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired

from web.database import db_session
from web.models.user import User
# from . import app

mod = Blueprint('auth', __name__)

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# Creating our login form
class LoginForm(FlaskForm):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('index'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        user = db_session.query(User).filter_by(username=username).first()
        if user:
            if bcrypt.hashpw(password.encode('utf-8'), user.password.encode('utf-8')) == user.password:
                user.authenticated = True
                current_sessions = db_session.object_session(user)
                db_session.add(user)
                db_session.commit()
                login_user(user, remember=True)
                return redirect(url_for("index"))
            else:
                flash(
                    'Invalid username or password. Please try again.',
                    'danger')
                return render_template('login.html', form=form)
        else:
            flash(
                'Invalid username or password. Please try again.',
                'danger')
            return render_template('login.html', form=form)

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@mod.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))
