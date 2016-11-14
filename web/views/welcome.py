from flask import Blueprint, render_template

welcome_view = Blueprint('welcome', __name__)


@welcome_view.route('/')
def home():
    return render_template('welcome.html')
