from flask import Blueprint, render_template

import bcrypt
from flask import flash, redirect, request, url_for, g
from flask_login import current_user, login_user, logout_user, LoginManager, current_user
from flask_wtf import FlaskForm

from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired

from scoring_engine.db import db
from scoring_engine.models.user import User

from scoring_engine.web import app
mod = Blueprint('auth', __name__)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def get_current_user():
    g.user = current_user


# Creating our login form
class LoginForm(FlaskForm):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('admin.home'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.query(User).filter_by(username=username).first()
        if isinstance(user.password, str):
            hashed_pw = user.password.encode('utf-8')
        else:
            hashed_pw = user.password
        if user:
            if bcrypt.hashpw(password.encode('utf-8'), hashed_pw) == hashed_pw:
                user.authenticated = True
                db.save(user)
                current_sessions = db.session.object_session(user)
                login_user(user, remember=True)
                return redirect(url_for("admin.home"))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
                return render_template('login.html', form=form)
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@mod.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('auth.login'))
