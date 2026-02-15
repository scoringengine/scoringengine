import logging
import os

from flask import Flask
from flask_login import LoginManager

from scoring_engine.cache import agent_cache, cache
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.version import version_info

SECRET_KEY = os.urandom(128)


def create_app():
    app = Flask(__name__)

    app.config.update(DEBUG=config.debug)
    app.config.update(UPLOAD_FOLDER=config.upload_folder)
    app.secret_key = SECRET_KEY

    # Static file caching: 1 hour in debug mode, 1 week in production
    # Browsers will cache CSS/JS/images and not re-request until max-age expires
    if config.debug:
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # 1 hour
    else:
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800  # 1 week

    # Configure Flask-SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = config.db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,  # Verify connections before using them
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    }

    # Initialize Flask-SQLAlchemy with the app
    db.init_app(app)

    if not config.debug:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    from scoring_engine.web.views import (
        about,
        admin,
        api,
        auth,
        flags,
        injects,
        notifications,
        overview,
        profile,
        scoreboard,
        services,
        stats,
        welcome,
        announcements,
    )

    cache.init_app(app)
    agent_cache.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    # Register the user_loader function after initializing login_manager
    from scoring_engine.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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
    app.register_blueprint(announcements.mod)

    @app.context_processor
    def inject_version():
        return {'version_info': version_info}

    return app
