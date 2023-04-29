from flask import Blueprint, render_template

from scoring_engine.models.setting import Setting

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    return render_template('welcome.html')
