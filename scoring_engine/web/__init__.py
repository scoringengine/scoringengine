import os
import logging

from flask import Flask
from flask_login import LoginManager

from scoring_engine.cache import cache
from scoring_engine.config import config


SECRET_KEY = os.urandom(128)


def create_app():
    app = Flask(__name__)

    app.config.update(DEBUG=config.debug)
    app.config.update(UPLOAD_FOLDER=config.upload_folder)
    app.secret_key = SECRET_KEY

    if not config.debug:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    from scoring_engine.web.views import (
        welcome,
        services,
        stats,
        scoreboard,
        profile,
        overview,
        notifications,
        injects,
        flags,
        auth,
        api,
        admin,
        about,
    )

    cache.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    # Register the user_loader function after initializing login_manager
    from scoring_engine.db import session
    from scoring_engine.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return session.query(User).get(int(user_id))

    app.register_blueprint(welcome.mod)
    app.register_blueprint(services.mod)
    app.register_blueprint(stats.mod)
    app.register_blueprint(scoreboard.mod)
    app.register_blueprint(profile.mod)
    app.register_blueprint(overview.mod)
    app.register_blueprint(notifications.mod)
    app.register_blueprint(injects.mod)
    app.register_blueprint(auth.mod)
    app.register_blueprint(flags.mod)
    app.register_blueprint(api.mod)
    app.register_blueprint(admin.mod)
    app.register_blueprint(about.mod)

    return app
