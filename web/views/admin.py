from flask import Blueprint, render_template

admin_blueprint = Blueprint('admin', __name__)


@admin_blueprint.route('/admin')
def home():
    return render_template('admin.html')
