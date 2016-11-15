import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from web.views import welcome, scoreboard, overview, services, admin
# from web.views import auth


app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

app.register_blueprint(welcome.mod)
app.register_blueprint(scoreboard.mod)
app.register_blueprint(overview.mod)
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
# app.register_blueprint(auth.mod)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.secret_key = os.urandom(128)
db = SQLAlchemy(app)
db.create_all()
