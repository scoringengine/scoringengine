from flask import Blueprint, render_template

import bcrypt
from flask import flash, redirect, request, url_for, g
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_wtf import FlaskForm

from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired

from scoring_engine.db import db
from scoring_engine.models.user import User

from scoring_engine.web import app
mod = Blueprint('auth', __name__)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def get_current_user():
    g.user = current_user


# Creating our login form
class LoginForm(FlaskForm):
    username = TextField('inputUsername', [InputRequired()], render_kw={"class": "form-control", "placeholder": "Username", "required": "true", "autofocus": "true"})
    password = PasswordField('inputUsername', [InputRequired()], render_kw={"class": "form-control", "placeholder": "Password", "required": "true"})


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('admin.status'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(User.username == username).one()

        if user:
            # Monkey Patch
            # Fixing the error where bmyers was getting a bytes type returned from user.password and rbower was getting str
            if isinstance(user.password, str):
                hashed_pw = user.password.encode('utf-8')
            else:
                hashed_pw = user.password

            if bcrypt.hashpw(password.encode('utf-8'), hashed_pw) == hashed_pw:
                user.authenticated = True
                db.save(user)
                login_user(user, remember=True)
                return redirect(url_for("admin.status"))
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
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('auth.login'))
