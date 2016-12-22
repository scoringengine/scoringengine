from flask import Blueprint, render_template
from scoring_engine.engine.config import config

mod = Blueprint('welcome', __name__)


@mod.route('/')
@mod.route("/index")
def home():
    sponsorship_images = config.sponsorship_images
    return render_template('welcome.html', sponsorship_images=sponsorship_images)
