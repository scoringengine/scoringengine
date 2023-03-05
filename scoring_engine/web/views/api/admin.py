import json
import pytz

from tempfile import template

from datetime import datetime, timezone
from dateutil.parser import parse
from flask import flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_required

import html

from scoring_engine.config import config
from scoring_engine.db import session
from scoring_engine.models.inject import Template, Inject
from scoring_engine.models.service import Service
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.setting import Setting
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.cache_helper import (
    update_scoreboard_data,
    update_overview_data,
    update_services_navbar,
    update_service_data,
    update_team_stats,
    update_services_data,
)
from scoring_engine.celery_stats import CeleryStats

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func



from . import mod


@mod.route("/api/admin/update_environment_info", methods=["POST"])
@login_required
def admin_update_environment():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            environment = session.query(Environment).get(int(request.form["pk"]))
            if environment:
                if request.form["name"] == "matching_content":
                    environment.matching_content = html.escape(request.form["value"])
                session.add(environment)
                session.commit()
                return jsonify({"status": "Updated Environment Information"})
            return jsonify({"error": "Incorrect permissions"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_property", methods=["POST"])
@login_required
def admin_update_property():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            property_obj = session.query(Property).get(int(request.form["pk"]))
            if property_obj:
                if request.form["name"] == "property_name":
                    property_obj.name = html.escape(request.form["value"])
                elif request.form["name"] == "property_value":
                    property_obj.value = html.escape(request.form["value"])
                session.add(property_obj)
                session.commit()
                return jsonify({"status": "Updated Property Information"})
            return jsonify({"error": "Incorrect permissions"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_check", methods=["POST"])
@login_required
def admin_update_check():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            check = session.query(Check).get(int(request.form["pk"]))
            if check:
                modified_check = False
                if request.form["name"] == "check_value":
                    if request.form["value"] == "1":
                        check.result = True
                    elif request.form["value"] == "2":
                        check.result = False
                    modified_check = True
                elif request.form["name"] == "check_reason":
                    modified_check = True
                    check.reason = request.form["value"]
                if modified_check:
                    session.add(check)
                    session.commit()
                    update_scoreboard_data()
                    update_overview_data()
                    update_services_navbar(check.service.team.id)
                    update_team_stats(check.service.team.id)
                    update_services_data(check.service.team.id)
                    update_service_data(check.service.id)
                    return jsonify({"status": "Updated Property Information"})
            return jsonify({"error": "Incorrect permissions"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_host", methods=["POST"])
@login_required
def admin_update_host():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            service = session.query(Service).get(int(request.form["pk"]))
            if service:
                if request.form["name"] == "host":
                    service.host = html.escape(request.form["value"])
                    session.add(service)
                    session.commit()
                    update_overview_data()
                    update_services_data(service.team.id)
                    update_service_data(service.id)
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_port", methods=["POST"])
@login_required
def admin_update_port():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            service = session.query(Service).get(int(request.form["pk"]))
            if service:
                if request.form["name"] == "port":
                    service.port = int(request.form["value"])
                    session.add(service)
                    session.commit()
                    update_overview_data()
                    update_services_data(service.team.id)
                    update_service_data(service.id)
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_worker_queue", methods=["POST"])
@login_required
def admin_update_worker_queue():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            service = session.query(Service).get(int(request.form["pk"]))
            if service:
                if request.form["name"] == "worker_queue":
                    service.worker_queue = request.form["value"]
                    session.add(service)
                    session.commit()
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_points", methods=["POST"])
@login_required
def admin_update_points():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            service = session.query(Service).get(int(request.form["pk"]))
            if service:
                if request.form["name"] == "points":
                    service.points = int(request.form["value"])
                    session.add(service)
                    session.commit()
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_about_page_content", methods=["POST"])
@login_required
def admin_update_about_page_content():
    if current_user.is_white_team:
        if "about_page_content" in request.form:
            setting = Setting.get_setting("about_page_content")
            setting.value = request.form["about_page_content"]
            session.add(setting)
            session.commit()
            flash("About Page Content Successfully Updated.", "success")
            return redirect(url_for("admin.settings"))
        flash("Error: about_page_content not specified.", "danger")
        return redirect(url_for("admin.manage"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_welcome_page_content", methods=["POST"])
@login_required
def admin_update_welcome_page_content():
    if current_user.is_white_team:
        if "welcome_page_content" in request.form:
            setting = Setting.get_setting("welcome_page_content")
            setting.value = request.form["welcome_page_content"]
            session.add(setting)
            session.commit()
            flash("Welcome Page Content Successfully Updated.", "success")
            return redirect(url_for("admin.settings"))
        flash("Error: welcome_page_content not specified.", "danger")
        return redirect(url_for("admin.manage"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_target_round_time", methods=["POST"])
@login_required
def admin_update_target_round_time():
    if current_user.is_white_team:
        if "target_round_time" in request.form:
            setting = Setting.get_setting("target_round_time")
            input_time = request.form["target_round_time"]
            if not input_time.isdigit():
                flash("Error: Target Round Time must be an integer.", "danger")
                return redirect(url_for("admin.settings"))
            setting.value = input_time
            session.add(setting)
            session.commit()
            flash("Target Round Time Successfully Updated.", "success")
            return redirect(url_for("admin.settings"))
        flash("Error: target_round_time not specified.", "danger")
        return redirect(url_for("admin.settings"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_worker_refresh_time", methods=["POST"])
@login_required
def admin_update_worker_refresh_time():
    if current_user.is_white_team:
        if "worker_refresh_time" in request.form:
            setting = Setting.get_setting("worker_refresh_time")
            input_time = request.form["worker_refresh_time"]
            if not input_time.isdigit():
                flash("Error: Worker Refresh Time must be an integer.", "danger")
                return redirect(url_for("admin.settings"))
            setting.value = input_time
            session.add(setting)
            session.commit()
            flash("Worker Refresh Time Successfully Updated.", "success")
            return redirect(url_for("admin.settings"))
        flash("Error: worker_refresh_time not specified.", "danger")
        return redirect(url_for("admin.settings"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_edit_hostname", methods=["POST"])
@login_required
def admin_update_blueteam_edit_hostname():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_update_hostname")
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_edit_port", methods=["POST"])
@login_required
def admin_update_blueteam_edit_port():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_update_port")
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_edit_account_usernames", methods=["POST"])
@login_required
def admin_update_blueteam_edit_account_usernames():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_update_account_usernames")
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_edit_account_passwords", methods=["POST"])
@login_required
def admin_update_blueteam_edit_account_passwords():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_update_account_passwords")
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_view_check_output", methods=["POST"])
@login_required
def admin_update_blueteam_view_check_output():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_view_check_output")
        print(setting.__dict__)
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        session.add(setting)
        session.commit()
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_round_progress")
@login_required
def get_check_progress_total():
    if current_user.is_white_team:
        task_id_settings = (
            session.query(KB)
            .filter_by(name="task_ids")
            .order_by(KB.round_num.desc())
            .first()
        )
        total_stats = {}
        total_stats["finished"] = 0
        total_stats["pending"] = 0

        team_stats = {}
        if task_id_settings:
            task_dict = json.loads(task_id_settings.value)
            for team_name, task_ids in task_dict.items():
                for task_id in task_ids:
                    task = execute_command.AsyncResult(task_id)
                    if team_name not in team_stats:
                        team_stats[team_name] = {}
                        team_stats[team_name]["pending"] = 0
                        team_stats[team_name]["finished"] = 0

                    if task.state == "PENDING":
                        team_stats[team_name]["pending"] += 1
                        total_stats["pending"] += 1
                    else:
                        team_stats[team_name]["finished"] += 1
                        total_stats["finished"] += 1

        total_percentage = 0
        total_tasks = total_stats["finished"] + total_stats["pending"]
        if total_stats["finished"] == 0:
            total_percentage = 0
        elif total_tasks == 0:
            total_percentage = 100
        elif total_stats and total_stats["finished"]:
            total_percentage = int((total_stats["finished"] / total_tasks) * 100)

        output_dict = {"Total": total_percentage}
        for team_name, team_stat in team_stats.items():
            team_total_percentage = 0
            team_total_tasks = team_stat["finished"] + team_stat["pending"]
            if team_stat["finished"] == 0:
                team_total_percentage = 0
            elif team_total_tasks == 0:
                team_total_percentage = 100
            elif team_stat and team_stat["finished"]:
                team_total_percentage = int(
                    (team_stat["finished"] / team_total_tasks) * 100
                )
            output_dict[team_name] = team_total_percentage

        return json.dumps(output_dict)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/injects/templates/<template_id>")
@login_required
def admin_get_inject_templates_id(template_id):
    if current_user.is_white_team:
        template = session.query(Template).get(int(template_id))
        data = dict(
            id=template.id,
            title=template.title,
            scenario=template.scenario,
            deliverable=template.deliverable,
            score=template.score,
            start_time=template.start_time.astimezone(
                pytz.timezone(config.timezone)
            ).isoformat(),
            end_time=template.end_time.astimezone(
                pytz.timezone(config.timezone)
            ).isoformat(),
            enabled=template.enabled,
            # rubric=[
            #     {"id": x.id, "value": x.value, "deliverable": x.deliverable}
            #     for x in template.rubric
            # ],
            teams=[inject.team.name for inject in template.inject if inject.enabled],
        )
        return jsonify(data)
    else:
        return jsonify({"status": "Unauthorized"}), 403


@mod.route("/api/admin/injects/templates/<template_id>", methods=["PUT"])
@login_required
def admin_put_inject_templates_id(template_id):
    if current_user.is_white_team:
        data = request.get_json()
        template = session.query(Template).get(int(template_id))
        if template:
            if data.get("title"):
                template.title = data["title"]
            if data.get("scenario"):
                template.scenario = data["scenario"]
            if data.get("deliverable"):
                template.deliverable = data["deliverable"]
            if data.get("start_time"):
                template.start_time = (
                    parse(data["start_time"]).astimezone(pytz.utc).replace(tzinfo=None)
                )
            if data.get("end_time"):
                template.end_time = (
                    parse(data["end_time"]).astimezone(pytz.utc).replace(tzinfo=None)
                )
            # TODO - Fix this to not be string values from javascript select
            if data.get("status") == "Enabled":
                template.enabled = True
            elif data.get("status") == "Disabled":
                template.enabled = False
            if data.get("score"):
                template.score = data["score"]
            if data.get("selectedTeams"):
                for team_name in data["selectedTeams"]:
                    inject = (
                        session.query(Inject)
                        .join(Template)
                        .join(Team)
                        .filter(Team.name == team_name)
                        .filter(Template.id == template_id)
                        .one_or_none()
                    )
                    # Update inject if it exists
                    if inject:
                        inject.enabled = True
                    # Otherwise, create the inject
                    else:
                        team = (
                            session.query(Team).filter(Team.name == team_name).first()
                        )
                        inject = Inject(
                            team=team,
                            template=template,
                        )
                        session.add(inject)
            if data.get("unselectedTeams"):
                injects = (
                    session.query(Inject)
                    .join(Template)
                    .join(Team)
                    .filter(Team.name.in_(data["unselectedTeams"]))
                    .filter(Template.id == template_id)
                    .all()
                )
                for inject in injects:
                    inject.enabled = False
            # TODO - Rubric updates
            session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Template not found"}), 400

    else:
        return jsonify({"status": "Unauthorized"}), 403


@mod.route("/api/admin/injects/templates/<template_id>", methods=["DELETE"])
@login_required
def admin_delete_inject_templates_id(template_id):
    if current_user.is_white_team:
        template = session.query(Template).get(int(template_id))
        if template:
            session.delete(template)
            session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Template not found"}), 400
    else:
        return jsonify({"status": "Unauthorized"}), 403


@mod.route("/api/admin/injects/templates")
@login_required
def admin_get_inject_templates():
    if current_user.is_white_team:
        data = list()
        templates = session.query(Template).options(joinedload(Template.inject)).all()
        for template in templates:
            data.append(
                dict(
                    id=template.id,
                    title=template.title,
                    scenario=template.scenario,
                    deliverable=template.deliverable,
                    score=template.score,
                    start_time=template.start_time.astimezone(
                        pytz.timezone(config.timezone)
                    ).isoformat(),
                    end_time=template.end_time.astimezone(
                        pytz.timezone(config.timezone)
                    ).isoformat(),
                    enabled=template.enabled,
                    # rubric=[
                    #     {"id": x.id, "value": x.value, "deliverable": x.deliverable}
                    #     for x in template.rubric
                    # ],
                    teams=[
                        inject.team.name
                        for inject in template.inject
                        if inject
                        if inject.enabled
                        if inject.team
                    ],
                )
            )
        return jsonify(data=data)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/inject/<inject_id>/grade", methods=["POST"])
@login_required
def admin_post_inject_grade(inject_id):
    if current_user.is_white_team:
        data = request.get_json()
        if "score" in data.keys() and data.get("score") != "":
            inject = session.query(Inject).get(inject_id)
            if inject:
                inject.graded = datetime.utcnow()
                inject.status = "Graded"
                inject.score = data.get("score")
                session.add(inject)
                session.commit()
                return jsonify({"status": "Success"}), 200
            else:
                return jsonify({"status": "Invalid Inject ID"}), 400
        else:
            return jsonify({"status": "Invalid Score Provided"}), 400
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/injects/templates", methods=["POST"])
@login_required
def admin_post_inject_templates():
    if current_user.is_white_team:
        data = request.get_json()
        if (
            data.get("title")
            and data.get("scenario")
            and data.get("deliverable")
            and data.get("score")
            and data.get("start_time")
            and data.get("end_time")
        ):
            template = Template(
                title=data["title"],
                scenario=data["scenario"],
                deliverable=data["deliverable"],
                score=data["score"],
                start_time=(
                    parse(data["start_time"])
                    .astimezone(pytz.timezone(config.timezone))
                    .replace(tzinfo=None)
                ),
                end_time=(
                    parse(data["end_time"])
                    .astimezone(pytz.timezone(config.timezone))
                    .replace(tzinfo=None)
                ),
            )
            session.add(template)
            session.commit()
            # TODO - Fix this to not be string values from javascript select
            if data.get("status") == "Enabled":
                template.enabled = True
            elif data.get("status") == "Disabled":
                template.enabled = False
            if data.get("selectedTeams"):
                for team_name in data["selectedTeams"]:
                    inject = (
                        session.query(Inject)
                        .join(Template)
                        .join(Team)
                        .filter(Team.name == team_name)
                        .filter(Template.id == template.id)
                        .one_or_none()
                    )
                    # Update inject if it exists
                    if inject:
                        inject.enabled = True
                    # Otherwise, create the inject
                    else:
                        team = (
                            session.query(Team).filter(Team.name == team_name).first()
                        )
                        inject = Inject(
                            team=team,
                            template=template,
                        )
                        session.add(inject)
            if data.get("unselectedTeams"):
                injects = (
                    session.query(Inject)
                    .join(Template)
                    .join(Team)
                    .filter(Team.name.in_(data["unselectedTeams"]))
                    .filter(Template.id == template.id)
                    .all()
                )
                for inject in injects:
                    inject.enabled = False
            session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Missing Data"}), 400
    else:
        return {"status": "Unauthorized"}, 403


# @mod.route("/api/admin/injects/templates/export")
# @login_required
# def admin_export_inject_templates():
#     if current_user.is_white_team:
#         data = []
#         templates = session.query(Template).all()
#         for template in templates:
#             data.append(
#                 dict(
#                     id=template.id,
#                     title=template.title,
#                     scenario=template.scenario,
#                     deliverable=template.deliverable,
#                     start_time=template.start_time,
#                     end_time=template.end_time,
#                     enabled=template.enabled,
#                     rubric=[
#                         {"id": x.id, "value": x.value, "deliverable": x.deliverable}
#                         for x in template.rubric
#                     ],
#                     # TODO - export teams
#                 )
#             )
#         return jsonify(data=data)
#     else:
#         return {"status": "Unauthorized"}, 403


# TODO - Generate injects from templates
@mod.route("/api/admin/injects/templates/import", methods=["POST"])
@login_required
def admin_import_inject_templates():
    if current_user.is_white_team:
        data = request.get_json()
        print(data)
        if data:
            for d in data:
                if d.get("id"):
                    template_id = d["id"]
                    t = session.query(Template).get(int(template_id))
                    # Update template if it exists
                    if t:
                        if d.get("title"):
                            t.title = d["title"]
                        if d.get("scenario"):
                            t.scenario = d["scenario"]
                        if d.get("deliverable"):
                            t.deliverable = d["deliverable"]
                        if d.get("start_time"):
                            t.start_time = (
                                parse(d["start_time"])
                                .astimezone(pytz.utc)
                                .replace(tzinfo=None)
                            )
                        if d.get("end_time"):
                            t.end_time = (
                                parse(d["start_time"])
                                .astimezone(pytz.utc)
                                .replace(tzinfo=None)
                            )
                        if d.get("enabled"):
                            t.enabled = True
                        else:
                            t.enabled = False
                        # for rubric in d["rubric"]:
                        #     if rubric.get("id"):
                        #         rubric_id = rubric["id"]
                        #     r = session.query(Rubric).get(int(rubric_id))
                        #     # Update rubric if it exists
                        #     if r:
                        #         if rubric.get("value"):
                        #             r.value = rubric["value"]
                        #         if rubric.get("deliverable"):
                        #             r.deliverable = rubric["deliverable"]
                        #     # Otherwise, create the rubric
                        #     else:
                        #         r = Rubric(
                        #             value=rubric["value"],
                        #             deliverable=rubric["deliverable"],
                        #             template=template,
                        #         )
                        #         session.add(r)
                        # Generate injects from template
                        if d.get("selectedTeams"):
                            for team_name in data["selectedTeams"]:
                                inject = (
                                    session.query(Inject)
                                    .join(Template)
                                    .join(Team)
                                    .filter(Team.name == team_name)
                                    .filter(Template.id == template_id)
                                    .one_or_none()
                                )
                                # Update inject if it exists
                                if inject:
                                    inject.enabled = True
                                # Otherwise, create the inject
                                else:
                                    team = (
                                        session.query(Team)
                                        .filter(Team.name == team_name)
                                        .first()
                                    )
                                    inject = Inject(
                                        team=team,
                                        template=template,
                                    )
                                    session.add(inject)
                        if d.get("unselectedTeams"):
                            injects = (
                                session.query(Inject)
                                .join(Template)
                                .join(Team)
                                .filter(Team.name.in_(data["unselectedTeams"]))
                                .filter(Template.id == template_id)
                                .all()
                            )
                            for inject in injects:
                                inject.enabled = False

                        session.commit()
                    else:
                        return (
                            jsonify(
                                {"status": "Error", "message": "Invalid Template ID"}
                            ),
                            400,
                        )
                # Otherwise, create the template
                else:
                    t = Template(
                        title=d["title"],
                        scenario=d["scenario"],
                        deliverable=d["deliverable"],
                        score=d["score"],
                        start_time=parse(d["start_time"])
                        .astimezone(pytz.utc)
                        .replace(tzinfo=None),
                        end_time=parse(d["end_time"])
                        .astimezone(pytz.utc)
                        .replace(tzinfo=None),
                        enabled=d["enabled"],
                    )
                    session.add(t)
                    # for rubric in d["rubric"]:
                    #     r = Rubric(
                    #         value=rubric["value"],
                    #         deliverable=rubric["deliverable"],
                    #         template=t,
                    #     )
                    #     session.add(r)
                    for team_name in d["teams"]:
                        inject = (
                            session.query(Inject)
                            .join(Template)
                            .join(Team)
                            .filter(Team.name == team_name)
                            .filter(Template.id == t.id)
                            .one_or_none()
                        )
                        # Update inject if it exists
                        if inject:
                            inject.enabled = True
                        # Otherwise, create the inject
                        else:
                            team = (
                                session.query(Team)
                                .filter(Team.name == team_name)
                                .first()
                            )
                            inject = Inject(
                                team=team,
                                template=t,
                            )
                            session.add(inject)
                    session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Invalid Data"}), 400
    else:
        return {"status": "Unauthorized"}, 403


# TODO - This is way too many database queries
@mod.route("/api/admin/injects/scores")
@login_required
def admin_inject_scores():
    if current_user.is_white_team:
        data = {}

        injects = (
            session.query(Inject)
            .options(joinedload(Inject.template))
            .order_by(Inject.template_id)
            .order_by(Inject.team_id)
            .all()
        )

        for inject in injects:
            if inject.template.id not in data:
                data[inject.template.id] = {
                    "title": inject.template.title,
                    "end_time": inject.template.end_time,
                }
            if inject.team.name not in data[inject.template.id]:
                data[inject.template.id][inject.team.name] = {
                    "id": inject.id,
                    "score": inject.score,
                    "status": inject.status,
                    "max_score": inject.template.score,
                }

        # Rewrite data to be in the format expected by the frontend
        score_data = []
        for x in data.items():
            score_data.append(x[1])

        return jsonify(data=score_data), 200
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/injects/get_bar_chart")
@login_required
def admin_injects_bar():
    if current_user.is_white_team:
        inject_scores = dict(
            session.query(Inject.team_id, func.sum(Inject.score))
            .filter(Inject.status == "Graded")
            .group_by(Inject.team_id)
            .all()
        )

        team_data = {}
        team_labels = []
        team_inject_scores = []
        blue_teams = (
            session.query(Team).filter(Team.color == "Blue").order_by(Team.name).all()
        )
        for blue_team in blue_teams:
            team_labels.append(blue_team.name)
            team_inject_scores.append(str(inject_scores.get(blue_team.id, 0)))

        team_data["labels"] = team_labels
        team_data["inject_scores"] = team_inject_scores

        return jsonify(team_data), 200
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/admin_update_template", methods=["POST"])
@login_required
def admin_update_template():
    if current_user.is_white_team:
        print(request.form)
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            template = session.query(Template).get(int(request.form["pk"]))
            if template:
                modified_check = False
                if request.form["name"] == "template_state":
                    template.state = request.form["value"]
                    modified_check = True
                elif request.form["name"] == "template_points":
                    template.points = request.form["value"]
                    modified_check = True
                if modified_check:
                    session.add(template)
                    session.commit()
                    # update_scoreboard_data()
                    # update_overview_data()
                    # update_services_navbar(check.service.team.id)
                    # update_team_stats(check.service.team.id)
                    # update_services_data(check.service.team.id)
                    # update_service_data(check.service.id)
                    return jsonify({"status": "Updated Property Information"})
            return jsonify({"error": "Template Not Found"})
    return jsonify({"error": "Incorrect permissions"})


# @mod.route("/api/admin/injects/team/<team_id>")
# @login_required
# def admin_get_team_injects(team_id):
#     if current_user.is_white_team:
#         injects = session.query(Inject).filter(team_id == team_id).all()
#         return jsonify(data=injects)
#     else:
#         return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_teams")
@login_required
def admin_get_teams():
    if current_user.is_white_team:
        all_teams = session.query(Team).all()
        data = []
        for team in all_teams:
            users = {}
            for user in team.users:
                users[user.username] = [user.password, str(user.authenticated).title()]
            data.append({"name": team.name, "color": team.color, "users": users})
        return jsonify(data=data)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_password", methods=["POST"])
@login_required
def admin_update_password():
    if current_user.is_white_team:
        if "user_id" in request.form and "password" in request.form:
            try:
                user_obj = (
                    session.query(User).filter(User.id == request.form["user_id"]).one()
                )
            except NoResultFound:
                return redirect(url_for("auth.login"))
            user_obj.update_password(html.escape(request.form["password"]))
            user_obj.authenticated = False
            session.add(user_obj)
            session.commit()
            flash("Password Successfully Updated.", "success")
            return redirect(url_for("admin.manage"))
        else:
            flash("Error: user_id or password not specified.", "danger")
            return redirect(url_for("admin.manage"))
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/add_user", methods=["POST"])
@login_required
def admin_add_user():
    if current_user.is_white_team:
        if (
            "username" in request.form
            and "password" in request.form
            and "team_id" in request.form
        ):
            team_obj = (
                session.query(Team).filter(Team.id == request.form["team_id"]).one()
            )
            user_obj = User(
                username=html.escape(request.form["username"]),
                password=html.escape(request.form["password"]),
                team=team_obj,
            )
            session.add(user_obj)
            session.commit()
            flash("User successfully added.", "success")
            return redirect(url_for("admin.manage"))
        else:
            flash("Error: Username, Password, or Team ID not specified.", "danger")
            return redirect(url_for("admin.manage"))
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/add_team", methods=["POST"])
@login_required
def admin_add_team():
    if current_user.is_white_team:
        if "name" in request.form and "color" in request.form:
            team_obj = Team(
                html.escape(request.form["name"]), html.escape(request.form["color"])
            )
            session.add(team_obj)
            session.commit()
            flash("Team successfully added.", "success")
            return redirect(url_for("admin.manage"))
        else:
            flash("Error: Team name or color not defined.", "danger")
            return redirect(url_for("admin.manage"))
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/toggle_engine", methods=["POST"])
@login_required
def admin_toggle_engine():
    if current_user.is_white_team:
        setting = Setting.get_setting("engine_paused")
        setting.value = not setting.value
        session.add(setting)
        session.commit()
        return {'status': "Success"}
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_engine_stats")
@login_required
def admin_get_engine_stats():
    if current_user.is_white_team:
        engine_stats = {}
        engine_stats["round_number"] = Round.get_last_round_num()
        engine_stats["num_passed_checks"] = (
            session.query(Check).filter_by(result=True).count()
        )
        engine_stats["num_failed_checks"] = (
            session.query(Check).filter_by(result=False).count()
        )
        engine_stats["total_checks"] = session.query(Check).count()
        return jsonify(engine_stats)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_engine_paused")
@login_required
def admin_get_engine_status():
    if current_user.is_white_team:
        return jsonify({"paused": Setting.get_setting("engine_paused").value})
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_worker_stats")
@login_required
def admin_get_worker_stats():
    if current_user.is_white_team:
        worker_stats = CeleryStats.get_worker_stats()
        return jsonify(data=worker_stats)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_queue_stats")
@login_required
def admin_get_queue_stats():
    if current_user.is_white_team:
        queue_stats = CeleryStats.get_queue_stats()
        return jsonify(data=queue_stats)
    else:
        return {"status": "Unauthorized"}, 403
