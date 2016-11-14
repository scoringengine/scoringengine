from flask import Blueprint, render_template

admin_view = Blueprint('admin', __name__)


@admin_view.route('/admin')
def home():
    return render_template('admin.html')
