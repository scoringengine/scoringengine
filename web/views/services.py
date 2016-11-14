from flask import Blueprint, render_template

services_view = Blueprint('services', __name__)


@services_view.route('/services')
def home():
    return render_template('services.html')


@services_view.route('/service/<id>')
def service(id):
    return render_template('service.html', service=id)
