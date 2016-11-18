from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user

mod = Blueprint('profile', __name__)


@mod.route('/profile')
@login_required
def home():
    return render_template('profile.html')
