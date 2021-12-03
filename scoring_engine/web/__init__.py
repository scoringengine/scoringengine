import os
import logging

from flask import Flask

from scoring_engine.cache import cache
from scoring_engine.config import config

app = Flask(__name__)

app.config.update(DEBUG=config.debug)
app.config.update(UPLOAD_FOLDER=config.upload_folder)
app.secret_key = os.urandom(128)

if not config.debug:
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

from scoring_engine.web.views import (
    welcome,
    scoreboard,
    overview,
    injects,
    services,
    admin,
    auth,
    profile,
    api,
    about,
)

cache.init_app(app)

app.register_blueprint(welcome.mod)
app.register_blueprint(scoreboard.mod)
app.register_blueprint(overview.mod)
app.register_blueprint(injects.mod)
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(auth.mod)
app.register_blueprint(profile.mod)
app.register_blueprint(api.mod)
app.register_blueprint(about.mod)
