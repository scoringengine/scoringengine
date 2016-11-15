from flask import Blueprint, render_template

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    return render_template('welcome.html')
