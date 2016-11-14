from flask import Flask

from web.views.welcome import welcome_view
from web.views.scoreboard import scoreboard_view
from web.views.overview import overview_view
from web.views.services import services_view
from web.views.admin import admin_view

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

app.register_blueprint(welcome_view)
app.register_blueprint(scoreboard_view)
app.register_blueprint(overview_view)
app.register_blueprint(services_view)
app.register_blueprint(admin_view)
