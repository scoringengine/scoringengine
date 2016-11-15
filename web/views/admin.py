from flask import Blueprint, render_template

mod = Blueprint('admin', __name__)


@mod.route('/admin')
def home():
    return render_template('admin.html')
