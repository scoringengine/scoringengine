from flask import Blueprint, render_template

mod = Blueprint("notifications", __name__)


@mod.route("/notifications")
@mod.route("/notifications/unread")
def unread():
    return render_template("notifications.html")


@mod.route("/notifications/read")
def read():
    return render_template("notifications.html")
