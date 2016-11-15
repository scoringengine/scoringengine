from flask import Blueprint, render_template

mod = Blueprint('services', __name__)


@mod.route('/services')
def home():
    return render_template('services.html')


@mod.route('/service/<id>')
def service(id):
    return render_template('service.html', service=id)
