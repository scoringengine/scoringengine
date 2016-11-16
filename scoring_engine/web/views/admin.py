from flask import Blueprint, render_template
from flask_login import login_required


mod = Blueprint('admin', __name__)


@mod.route('/admin')
@mod.route('/admin/status')
@login_required
def status():
    return render_template('admin/status.html')


@mod.route('/admin/manage')
@login_required
def manage():
    return render_template('admin/manage.html')


@mod.route('/admin/stats')
@login_required
def stats():
    return render_template('admin/stats.html')
