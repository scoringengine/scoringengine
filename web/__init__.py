import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from web.views.welcome import welcome_blueprint
from web.views.scoreboard import scoreboard_blueprint
from web.views.overview import overview_blueprint
from web.views.services import services_blueprint
from web.views.admin import admin_blueprint

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

app.register_blueprint(welcome_blueprint)
app.register_blueprint(scoreboard_blueprint)
app.register_blueprint(overview_blueprint)
app.register_blueprint(services_blueprint)
app.register_blueprint(admin_blueprint)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.secret_key = os.urandom(128)
db = SQLAlchemy(app)
db.create_all()
