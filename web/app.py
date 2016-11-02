import os
import sys
from flask import Flask, flash, g, jsonify, redirect, render_template, request, Response, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from flask_wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired

# Hacky way for us to import our users
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../scoring_engine'))
from models.user import User


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
app.secret_key = os.urandom(128)
db = SQLAlchemy(app)


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
class LoginForm(Form):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])


@app.route("/")
@login_required
def index():
    team1 = [0, 100, 200, 300, 400, 500]
    team2 = [0, 200, 300, 400, 400, 600]
    team3 = [0, 300, 300, 300, 300, 400]

    teamData = {
        "1": {
            "label": "Team 1",
            "data": team1
        },
        "2": {
            "label": "Team 2",
            "data": team2
        },
        "3": {
            "label": "Team 3",
            "data": team3
        }
    }

    return render_template('index.html', teamData=teamData)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('index'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query(username)
        if user:
            if user.check_hash(user.password, password):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for("index"))
        else:
            flash(
                'Invalid username or password. Please try again.',
                'danger')
            return render_template('login.html', form=form)

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

app.run(host="127.0.0.1", debug=True)