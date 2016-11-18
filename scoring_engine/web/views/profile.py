from flask import Blueprint, render_template
from flask_login import login_required

mod = Blueprint('profile', __name__)


@mod.route('/profile')
@login_required
def home():
    return render_template('profile.html')
