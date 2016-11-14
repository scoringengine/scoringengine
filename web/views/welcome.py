from flask import Blueprint, render_template

welcome_blueprint = Blueprint('welcome', __name__)


@welcome_blueprint.route('/')
@welcome_blueprint.route("/index")
def home():
    return render_template('welcome.html')
