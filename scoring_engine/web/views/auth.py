from flask import Blueprint, render_template

import bcrypt
from flask import flash, redirect, request, url_for, g
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_wtf import FlaskForm

from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired

from sqlalchemy.orm.exc import NoResultFound

from scoring_engine.db import db
from scoring_engine.models.user import User

from scoring_engine.web import app
mod = Blueprint('auth', __name__)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(session_token):
    return User.query.filter_by(session_token=session_token).first()


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

        try:
            user = User.query.filter(User.username == username).one()
        except NoResultFound:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

        if user:
            # Monkey Patch
            # Fixing the error where bmyers was getting a bytes returned from user.password and rbower was getting str
            if isinstance(user.password, str):
                hashed_pw = user.password.encode('utf-8')
            else:
                hashed_pw = user.password

            if bcrypt.hashpw(password.encode('utf-8'), hashed_pw) == hashed_pw:
                user.authenticated = True
                user.session_token = user.generate_session_token()
                db.save(user)
                login_user(user, remember=True)
                if user.is_white_team:
                    return redirect(url_for("admin.status"))
                elif user.is_blue_team:
                    return redirect(url_for("services.home"))
                else:
                    return redirect(url_for("overview.home"))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
                return render_template('login.html', form=form)
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@mod.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')


@mod.route('/logout')
@login_required
def logout():
    try:
        user = User.query.filter(User.username == current_user.username).one()
    except NoResultFound:
        return redirect(url_for('auth.login'))
    user.authenticated = False
    db.save(user)
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('auth.login'))
