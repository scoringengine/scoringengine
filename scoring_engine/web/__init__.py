import os

from flask import Flask
from scoring_engine.web.cache import cache

app = Flask(__name__)
cache.init_app(app)
app.config.from_pyfile('settings.cfg')
app.secret_key = os.urandom(128)

from scoring_engine.web.views import welcome, scoreboard, overview, services, admin, auth, profile, api

app.register_blueprint(welcome.mod)
app.register_blueprint(scoreboard.mod)
app.register_blueprint(overview.mod)
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(auth.mod)
app.register_blueprint(profile.mod)
app.register_blueprint(api.mod)
