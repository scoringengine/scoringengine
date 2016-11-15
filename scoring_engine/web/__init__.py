import os

from flask import Flask, g
from flask_login import LoginManager, current_user

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

from scoring_engine.web.views import welcome, scoreboard, overview, services, admin, auth

app.register_blueprint(welcome.mod)
app.register_blueprint(scoreboard.mod)
app.register_blueprint(overview.mod)
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(auth.mod)

app.secret_key = os.urandom(128)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


from scoring_engine.models.user import User


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def get_current_user():
    g.user = current_user
