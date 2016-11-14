from flask import Blueprint, render_template

services_blueprint = Blueprint('services', __name__)


@services_blueprint.route('/services')
def home():
    return render_template('services.html')


@services_blueprint.route('/service/<id>')
def service(id):
    return render_template('service.html', service=id)
