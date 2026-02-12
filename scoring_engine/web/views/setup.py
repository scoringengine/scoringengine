import os
import yaml

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session as flask_session,
    send_file,
)

from scoring_engine.db import session as db_session
from scoring_engine.engine.engine import Engine
from scoring_engine.competition import Competition

mod = Blueprint("setup", __name__)


def competition_file_path():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "..",
            "bin",
            "competition.yaml",
        )
    )


@mod.route("/setup", methods=["GET", "POST"])
def setup():
    comp_path = competition_file_path()
    step = int(request.args.get("step", 1))
    data = flask_session.get("setup", {})

    if step == 1:
        if request.method == "POST":
            data["admin"] = {
                "username": request.form.get("username", "admin"),
                "password": request.form.get("password", "changeme"),
            }
            flask_session["setup"] = data
            return redirect(url_for("setup.setup", step=2))
        return render_template("setup.html", step=1)

    if step == 2:
        if request.method == "POST":
            data["num_teams"] = int(request.form.get("num_teams", 1))
            flask_session["setup"] = data
            return redirect(url_for("setup.setup", step=3))
        return render_template("setup.html", step=2)

    if step == 3:
        checks_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "checks")
        )
        available_checks = Engine.load_check_files(checks_dir)
        check_names = [c.__name__ for c in available_checks]
        if request.method == "POST":
            service = {
                "name": request.form.get("service_name"),
                "check_name": request.form.get("check_name"),
                "host": request.form.get("host"),
                "port": int(request.form.get("port", 0)),
                "points": int(request.form.get("points", 100)),
            }
            matching_content = request.form.get("matching_content", "SUCCESS")
            props_raw = request.form.get("properties", "")
            properties = []
            for line in props_raw.splitlines():
                if line.strip():
                    key, value = line.split("=", 1)
                    properties.append({"name": key.strip(), "value": value.strip()})
            env = {"matching_content": matching_content}
            if properties:
                env["properties"] = properties
            service["environments"] = [env]
            services = data.get("services", [])
            services.append(service)
            data["services"] = services
            flask_session["setup"] = data
            if request.form.get("action") == "finish":
                teams = [
                    {
                        "name": "White Team",
                        "color": "White",
                        "users": [
                            {
                                "username": data["admin"]["username"],
                                "password": data["admin"]["password"],
                            }
                        ],
                    }
                ]
                services_config = data.get("services", [])
                for i in range(1, data.get("num_teams", 1) + 1):
                    teams.append(
                        {
                            "name": f"Team {i}",
                            "color": "Blue",
                            "users": [
                                {
                                    "username": f"team{i}user1",
                                    "password": "changeme",
                                }
                            ],
                            "services": services_config,
                        }
                    )

                competition_dict = {"teams": teams, "flags": []}
                yaml_str = yaml.dump(competition_dict, sort_keys=False)
                os.makedirs(os.path.dirname(comp_path), exist_ok=True)
                with open(comp_path, "w") as f:
                    f.write(yaml_str)
                competition = Competition.parse_yaml_str(yaml_str)
                competition.save(db_session)
                return redirect(url_for("setup.setup", step=4))
            return redirect(url_for("setup.setup", step=3))
        return render_template(
            "setup.html", step=3, checks=check_names, services=data.get("services", [])
        )

    competition_exists = os.path.exists(comp_path)
    return render_template("setup.html", step=4, competition_exists=competition_exists)


@mod.route("/setup/export")
def export():
    comp_path = competition_file_path()
    if os.path.exists(comp_path):
        return send_file(comp_path, as_attachment=True, download_name="competition.yaml")
    return redirect(url_for("setup.setup"))

