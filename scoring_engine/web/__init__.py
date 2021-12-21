import os
import logging
from flask import Flask
from easy_profile import EasyProfileMiddleware


from scoring_engine.cache import cache
from scoring_engine.config import config


app = Flask(__name__)

app.config.update(DEBUG=config.debug)
app.secret_key = os.urandom(128)

if not config.debug:
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
else:
    app.wsgi_app = EasyProfileMiddleware(app.wsgi_app)  # Enable database profiler

from scoring_engine.web.views import (
    welcome,
    scoreboard,
    overview,
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
app.register_blueprint(services.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(auth.mod)
app.register_blueprint(profile.mod)
app.register_blueprint(api.mod)
app.register_blueprint(about.mod)
