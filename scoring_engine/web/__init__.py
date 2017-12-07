import os

import logging
from flask import Flask


app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
app.secret_key = os.urandom(128)


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from scoring_engine.web.views import welcome, scoreboard, overview, services, admin, auth, profile, api, about

app.register_blueprint(welcome.mod)
app.register_blueprint(scoreboard.mod)
app.register_blueprint(overview.mod)
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(auth.mod)
app.register_blueprint(profile.mod)
app.register_blueprint(api.mod)
app.register_blueprint(about.mod)
