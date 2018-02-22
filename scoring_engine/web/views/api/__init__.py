from flask import Blueprint


mod = Blueprint('api', __name__)


from . import admin
from . import overview
from . import profile
from . import scoreboard
from . import service
from . import team
