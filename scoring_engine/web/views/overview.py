from flask import Blueprint, render_template

mod = Blueprint("overview", __name__)


@mod.route("/overview")
def home():
    return render_template("overview.html")
