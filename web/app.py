import bcrypt
import os
import sys
from flask import Flask, flash, g, jsonify, redirect, render_template, request, Response, url_for
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.secret_key = os.urandom(128)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(50), nullable=False)
    #team_id = Column(Integer, ForeignKey('teams.id'))
    #team = relationship("Team", back_populates="users")
    authenticated = Column(Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % self.username


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


@app.route("/")
@app.route("/index")
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


@app.route('/team/<string:team>')
@login_required
def team(team):
    return str(team)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('index'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.query(User).filter_by(username=username).first()
        if user:
            if bcrypt.hashpw(password.encode('utf-8'), user.password.encode('utf-8')) == user.password:
                user.authenticated = True
                current_sessions = db.session.object_session(user)
                db.session.add(user)
                db.session.commit()
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


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    db.create_all()
    #user = User('test', 'test')
    #db.session.add(user)
    #db.session.commit()
    app.run(host="127.0.0.1", debug=True)
