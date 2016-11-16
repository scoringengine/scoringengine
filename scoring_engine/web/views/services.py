from flask import Blueprint, render_template
from flask_login import login_required

mod = Blueprint('services', __name__)


@mod.route('/services')
def home():
    return render_template('services.html')


@mod.route('/service/<id>')
@login_required
def service(id):
    return render_template('service.html', service=id)
