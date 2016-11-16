from flask import Blueprint, render_template
from flask_login import login_required


mod = Blueprint('admin', __name__)


@mod.route('/admin')
@login_required
def home():
    return render_template('admin.html')
