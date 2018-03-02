import uuid
from flask import flash, redirect, request, url_for, g, Blueprint, render_template
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_wtf import FlaskForm

from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired

from sqlalchemy.orm.exc import NoResultFound

from scoring_engine.db import session
from scoring_engine.models.user import User

from scoring_engine.web import app

mod = Blueprint('auth', __name__)
mod.secret_key = str(uuid.uuid4())

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'


@login_manager.user_loader
def load_user(id):
    return session.query(User).get(int(id))


@app.before_request
def get_current_user():
    g.user = current_user


# Creating our login form
class LoginForm(FlaskForm):
    username = StringField('inputUsername', [InputRequired()], render_kw={"class": "form-control", "placeholder": "Username", "required": "true", "autofocus": "true"})
    password = PasswordField('inputUsername', [InputRequired()], render_kw={"class": "form-control", "placeholder": "Password", "required": "true"})


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for("welcome.home"))

    form = LoginForm()

    if form.errors:
        flash(form.errors, 'danger')
        return render_template('login.html', form=form)

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = session.query(User).filter(User.username == username).one()
        except NoResultFound:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

        if User.generate_hash(password, user.password) == user.password:
            user.authenticated = True
            session.add(user)
            session.commit()
            login_user(user, remember=True)

            if user.is_white_team:
                return redirect(request.values.get('next') or url_for("admin.status"))
            elif user.is_blue_team:
                return redirect(request.values.get('next') or url_for("services.home"))
            else:
                return redirect(request.values.get('next') or url_for("overview.home"))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@mod.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')


@mod.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    session.add(user)
    session.commit()
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('auth.login'))
