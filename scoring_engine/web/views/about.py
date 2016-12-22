from flask import Blueprint, render_template

mod = Blueprint('about', __name__)


@mod.route('/about')
def about():
    return render_template('about.html')
