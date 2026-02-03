from flask import Blueprint, render_template

mod = Blueprint("announcements", __name__)


@mod.route("/announcements")
def home():
    """Display announcements page. Data loaded client-side from cached API."""
    return render_template("announcements.html")
