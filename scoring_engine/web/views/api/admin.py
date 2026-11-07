import html
import io
import json
import os
import re
import time
import zipfile
from datetime import datetime, timezone

import pytz
from dateutil.parser import parse
from flask import flash, jsonify, redirect, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename

from scoring_engine.worker_packs import service_queue
from scoring_engine.cache_helper import (
    update_all_cache,
    update_all_inject_data,
    update_flags_data,
    update_inject_comments,
    update_inject_data,
    update_overview_data,
    update_scoreboard_data,
    update_service_data,
    update_services_data,
    update_services_navbar,
    update_team_stats,
)
from scoring_engine.celery_stats import CeleryStats
from scoring_engine.config import config
from scoring_engine.datetime_utils import ensure_utc_aware
from scoring_engine.db import db
from scoring_engine.engine.basic_check import CHECK_FAILURE_TEXT, CHECK_SUCCESS_TEXT, CHECK_TIMED_OUT_TEXT
from scoring_engine.engine.engine import Engine
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.events import publish_event
from scoring_engine.models.check import Check
from scoring_engine.models.competition_window import CompetitionWindow
from scoring_engine.models.environment import Environment
from scoring_engine.models.inject import Inject, InjectComment, InjectRubricScore, RubricItem, Template
from scoring_engine.models.kb import KB
from scoring_engine.models.property import Property
from scoring_engine.models.round import Round
from scoring_engine.models.round_score import RoundScore
from scoring_engine.models.score_adjustment import ScoreAdjustment
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.welcome import get_welcome_config, save_welcome_config
from scoring_engine.notifications import notify_inject_graded, notify_revision_requested
from scoring_engine.schedule import clear_windows_cache

from . import mod


@mod.route("/api/admin/update_environment_info", methods=["POST"])
@login_required
def admin_update_environment():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            environment = db.session.get(Environment, int(request.form["pk"]))
            if environment:
                if request.form["name"] in ("matching_content", "matching_content_reject"):
                    value = html.escape(request.form["value"])
                    if value:
                        try:
                            re.compile(value)
                        except re.error as e:
                            return jsonify({"error": "Invalid regex pattern: " + str(e)}), 400
                    setattr(environment, request.form["name"], value or None)
                db.session.add(environment)
                db.session.commit()
                return jsonify({"status": "Updated Environment Information"})
            return jsonify({"error": "Incorrect permissions"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_property", methods=["POST"])
@login_required
def admin_update_property():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            property_obj = db.session.get(Property, int(request.form["pk"]))
            if property_obj:
                if request.form["name"] == "property_name":
                    property_obj.name = html.escape(request.form["value"])
                elif request.form["name"] == "property_value":
                    property_obj.value = html.escape(request.form["value"])
                db.session.add(property_obj)
                db.session.commit()
                return jsonify({"status": "Updated Property Information"})
            return jsonify({"error": "Incorrect permissions"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_check", methods=["POST"])
@login_required
def admin_update_check():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            check = db.session.get(Check, int(request.form["pk"]))
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
                    db.session.add(check)
                    db.session.commit()
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
            service = db.session.get(Service, int(request.form["pk"]))
            if service:
                if request.form["name"] == "host":
                    service.host = html.escape(request.form["value"])
                    db.session.add(service)
                    db.session.commit()
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
            service = db.session.get(Service, int(request.form["pk"]))
            if service:
                if request.form["name"] == "port":
                    service.port = int(request.form["value"])
                    db.session.add(service)
                    db.session.commit()
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
            service = db.session.get(Service, int(request.form["pk"]))
            if service:
                if request.form["name"] == "worker_queue":
                    service.worker_queue = request.form["value"]
                    db.session.add(service)
                    db.session.commit()
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_points", methods=["POST"])
@login_required
def admin_update_points():
    if current_user.is_white_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            service = db.session.get(Service, int(request.form["pk"]))
            if service:
                if request.form["name"] == "points":
                    service.points = int(request.form["value"])
                    db.session.add(service)
                    db.session.commit()
                    return jsonify({"status": "Updated Service Information"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/update_about_page_content", methods=["POST"])
@login_required
def admin_update_about_page_content():
    if current_user.is_white_team:
        if "about_page_content" in request.form:
            setting = Setting.get_setting("about_page_content")
            setting.value = request.form["about_page_content"]
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("about_page_content")
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
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("welcome_page_content")
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
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("target_round_time")
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
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("worker_refresh_time")
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
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("blue_team_update_hostname")
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
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("blue_team_update_port")
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
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("blue_team_update_account_usernames")
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
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("blue_team_update_account_passwords")
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_blueteam_view_check_output", methods=["POST"])
@login_required
def admin_update_blueteam_view_check_output():
    if current_user.is_white_team:
        setting = Setting.get_setting("blue_team_view_check_output")
        if setting.value is True:
            setting.value = False
        else:
            setting.value = True
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("blue_team_view_check_output")
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_anonymize_team_names", methods=["POST"])
@login_required
def admin_update_anonymize_team_names():
    if current_user.is_white_team:
        setting = Setting.get_setting("anonymize_team_names")
        if setting is None:
            # Create the setting if it doesn't exist
            setting = Setting(name="anonymize_team_names", value=True)
        elif setting.value is True:
            setting.value = False
        else:
            setting.value = True
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")
        return redirect(url_for("admin.permissions"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/check/<int:check_id>/full_output")
@login_required
def admin_get_check_full_output(check_id):
    if current_user.is_white_team:
        check = db.session.get(Check, check_id)
        if not check:
            return jsonify({"error": "Check not found"}), 404

        team_name = check.service.team.name
        service_name = check.service.name
        round_num = check.round.number

        # Try disk file first, fall back to DB output
        output_path = os.path.join(
            config.check_output_folder,
            team_name,
            service_name,
            f"round_{round_num}.txt",
        )

        if os.path.isfile(output_path):
            with open(output_path, "r") as f:
                content = f.read()
        else:
            content = check.output or ""

        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_round_progress")
@login_required
def get_check_progress_total():
    if current_user.is_white_team:
        task_id_settings = db.session.query(KB).filter_by(name="task_ids").order_by(KB.round_num.desc()).first()
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
                team_total_percentage = int((team_stat["finished"] / team_total_tasks) * 100)
            output_dict[team_name] = team_total_percentage

        return json.dumps(output_dict)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/inject/<inject_id>/reopen", methods=["POST"])
@login_required
def admin_post_inject_reopen(inject_id):
    if current_user.is_white_team:
        inject = db.session.get(Inject, inject_id)
        if not inject:
            return jsonify({"status": "Invalid Inject ID"}), 400
        if inject.status != "Graded":
            return jsonify({"status": "Inject is not in Graded state"}), 400

        inject.status = "Submitted"
        inject.graded = None
        comment = InjectComment(
            f"Inject reopened for re-grading by {current_user.username}.",
            current_user,
            inject,
        )
        db.session.add(comment)
        db.session.commit()
        update_inject_data(inject_id)
        update_inject_comments(inject_id)
        update_scoreboard_data()
        publish_event("inject_update", {"inject_id": inject_id}, visibility="blue", team_id=inject.team_id)
        publish_event("inject_update", {"inject_id": inject_id}, visibility="white")
        return jsonify({"status": "Success"}), 200
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/injects/templates/<template_id>")
@login_required
def admin_get_inject_templates_id(template_id):
    if current_user.is_white_team:
        template = db.session.get(Template, int(template_id))
        data = dict(
            id=template.id,
            title=template.title,
            scenario=template.scenario,
            deliverable=template.deliverable,
            category=template.category,
            max_score=template.max_score,
            start_time=ensure_utc_aware(template.start_time).astimezone(pytz.timezone(config.timezone)).isoformat(),
            end_time=ensure_utc_aware(template.end_time).astimezone(pytz.timezone(config.timezone)).isoformat(),
            enabled=template.enabled,
            rubric_items=[
                {"id": x.id, "title": x.title, "description": x.description, "points": x.points, "order": x.order}
                for x in template.rubric_items
            ],
            teams=[inject.team.name for inject in template.injects if inject.enabled and inject.team],
        )
        return jsonify(data)
    else:
        return jsonify({"status": "Unauthorized"}), 403


@mod.route("/api/admin/injects/templates/<template_id>", methods=["PUT"])
@login_required
def admin_put_inject_templates_id(template_id):
    if current_user.is_white_team:
        data = request.get_json()
        template = db.session.get(Template, int(template_id))
        if template:
            if data.get("title"):
                template.title = data["title"]
            if data.get("scenario"):
                template.scenario = data["scenario"]
            if data.get("deliverable"):
                template.deliverable = data["deliverable"]
            if data.get("start_time"):
                template.start_time = parse(data["start_time"]).astimezone(pytz.utc).replace(tzinfo=None)
            if data.get("end_time"):
                template.end_time = parse(data["end_time"]).astimezone(pytz.utc).replace(tzinfo=None)
            if "category" in data:
                template.category = data["category"] or None
            # TODO - Fix this to not be string values from javascript select
            if data.get("status") == "Enabled":
                template.enabled = True
            elif data.get("status") == "Disabled":
                template.enabled = False
            if "rubric_items" in data:
                # Update existing rubric items in place to preserve scores
                existing_by_id = {item.id: item for item in template.rubric_items}
                incoming_ids = set()
                for idx, ri in enumerate(data["rubric_items"]):
                    ri_id = ri.get("id")
                    if ri_id and ri_id in existing_by_id:
                        # Update existing item
                        item = existing_by_id[ri_id]
                        item.title = ri["title"]
                        item.points = ri["points"]
                        item.description = ri.get("description")
                        item.order = ri.get("order", idx)
                        incoming_ids.add(ri_id)
                    else:
                        # Create new item
                        rubric_item = RubricItem(
                            title=ri["title"],
                            points=ri["points"],
                            template=template,
                            description=ri.get("description"),
                            order=ri.get("order", idx),
                        )
                        db.session.add(rubric_item)
                # Delete only items that were removed from the payload
                for item_id, item in existing_by_id.items():
                    if item_id not in incoming_ids:
                        db.session.delete(item)
            if data.get("selectedTeams"):
                for team_name in data["selectedTeams"]:
                    inject = (
                        db.session.query(Inject)
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
                        team = db.session.query(Team).filter(Team.name == team_name).first()
                        inject = Inject(
                            team=team,
                            template=template,
                        )
                        db.session.add(inject)
            if data.get("unselectedTeams"):
                injects = (
                    db.session.query(Inject)
                    .join(Template)
                    .join(Team)
                    .filter(Team.name.in_(data["unselectedTeams"]))
                    .filter(Template.id == template_id)
                    .all()
                )
                for inject in injects:
                    inject.enabled = False
            db.session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Template not found"}), 400

    else:
        return jsonify({"status": "Unauthorized"}), 403


@mod.route("/api/admin/injects/templates/<template_id>", methods=["DELETE"])
@login_required
def admin_delete_inject_templates_id(template_id):
    if current_user.is_white_team:
        template = db.session.get(Template, int(template_id))
        if template:
            db.session.delete(template)
            db.session.commit()
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
        templates = db.session.query(Template).options(joinedload(Template.injects)).all()
        for template in templates:
            data.append(
                dict(
                    id=template.id,
                    title=template.title,
                    category=template.category,
                    scenario=template.scenario,
                    deliverable=template.deliverable,
                    max_score=template.max_score,
                    start_time=template.start_time.astimezone(pytz.timezone(config.timezone)).isoformat(),
                    end_time=template.end_time.astimezone(pytz.timezone(config.timezone)).isoformat(),
                    enabled=template.enabled,
                    rubric_items=[
                        {
                            "id": x.id,
                            "title": x.title,
                            "description": x.description,
                            "points": x.points,
                            "order": x.order,
                        }
                        for x in template.rubric_items
                    ],
                    teams=[inject.team.name for inject in template.injects if inject if inject.enabled if inject.team],
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
        if "rubric_scores" not in data or not data["rubric_scores"]:
            return jsonify({"status": "Invalid Score Provided"}), 400
        inject = db.session.get(Inject, inject_id)
        if not inject:
            return jsonify({"status": "Invalid Inject ID"}), 400

        # Validate rubric items belong to the template
        template_item_ids = {item.id for item in inject.template.rubric_items}
        template_item_max = {item.id: item.points for item in inject.template.rubric_items}
        for rs in data["rubric_scores"]:
            if rs["rubric_item_id"] not in template_item_ids:
                return jsonify({"status": "Invalid rubric item ID"}), 400
            if rs["score"] > template_item_max[rs["rubric_item_id"]]:
                return jsonify({"status": "Score exceeds rubric item max"}), 400

        # Delete existing scores and create new ones
        for old_score in list(inject.rubric_scores):
            db.session.delete(old_score)
        db.session.flush()

        for rs in data["rubric_scores"]:
            rubric_item = db.session.get(RubricItem, rs["rubric_item_id"])
            score_obj = InjectRubricScore(
                score=rs["score"],
                inject=inject,
                rubric_item=rubric_item,
                grader=current_user,
            )
            db.session.add(score_obj)

        inject.graded = datetime.now(timezone.utc)
        inject.status = "Graded"
        score = sum(rs["score"] for rs in data["rubric_scores"])
        comment = InjectComment(
            f"Inject graded by {current_user.username}. Score: {score}/{inject.template.max_score}.",
            current_user,
            inject,
        )
        db.session.add(comment)
        db.session.commit()
        update_inject_data(inject_id)
        update_inject_comments(inject_id)
        update_scoreboard_data()
        publish_event("inject_update", {"inject_id": inject_id}, visibility="blue", team_id=inject.team_id)
        publish_event("inject_update", {"inject_id": inject_id}, visibility="white")
        notify_inject_graded(inject)
        return jsonify({"status": "Success"}), 200
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/inject/<inject_id>/request-revision", methods=["POST"])
@login_required
def admin_post_inject_request_revision(inject_id):
    if current_user.is_white_team:
        inject = db.session.get(Inject, inject_id)
        if not inject:
            return jsonify({"status": "Invalid Inject ID"}), 400
        if inject.status not in ("Submitted", "Resubmitted"):
            return jsonify({"status": "Inject is not in a submittable state"}), 400

        data = request.get_json() or {}
        reason = data.get("reason", "Revision requested by grader.")

        inject.status = "Revision Requested"
        # Create a system comment with the reason
        comment = InjectComment(content=reason, user=current_user, inject=inject)
        db.session.add(comment)
        db.session.commit()
        update_inject_data(inject_id)
        update_inject_comments(inject_id)
        publish_event("inject_update", {"inject_id": inject_id}, visibility="blue", team_id=inject.team_id)
        publish_event("inject_update", {"inject_id": inject_id}, visibility="white")
        notify_revision_requested(inject)
        return jsonify({"status": "Success"}), 200
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/injects/template/<int:template_id>/submissions")
@login_required
def admin_get_template_submissions(template_id):
    if current_user.is_white_team:
        template = db.session.get(Template, template_id)
        if not template:
            return jsonify({"status": "Template not found"}), 404

        submissions = []
        for inject in template.injects:
            if not inject.team or not inject.enabled:
                continue
            submissions.append(
                {
                    "id": inject.id,
                    "team": inject.team.name,
                    "status": inject.status,
                    "score": inject.score,
                    "max_score": template.max_score,
                    "submitted": inject.submitted.isoformat() if inject.submitted else None,
                    "graded": inject.graded.isoformat() if inject.graded else None,
                }
            )
        return jsonify(data=submissions), 200
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
            and data.get("start_time")
            and data.get("end_time")
        ):
            template = Template(
                title=data["title"],
                scenario=data["scenario"],
                deliverable=data["deliverable"],
                start_time=parse(data["start_time"]).astimezone(pytz.utc).replace(tzinfo=None),
                end_time=parse(data["end_time"]).astimezone(pytz.utc).replace(tzinfo=None),
                category=data.get("category"),
            )
            db.session.add(template)
            db.session.flush()
            # Create rubric items
            if data.get("rubric_items"):
                for i, item_data in enumerate(data["rubric_items"]):
                    rubric_item = RubricItem(
                        title=item_data["title"],
                        description=item_data.get("description", ""),
                        points=item_data["points"],
                        order=item_data.get("order", i),
                        template=template,
                    )
                    db.session.add(rubric_item)
            db.session.commit()
            # TODO - Fix this to not be string values from javascript select
            if data.get("status") == "Enabled":
                template.enabled = True
            elif data.get("status") == "Disabled":
                template.enabled = False
            if data.get("selectedTeams"):
                for team_name in data["selectedTeams"]:
                    inject = (
                        db.session.query(Inject)
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
                        team = db.session.query(Team).filter(Team.name == team_name).first()
                        inject = Inject(
                            team=team,
                            template=template,
                        )
                        db.session.add(inject)
            if data.get("unselectedTeams"):
                injects = (
                    db.session.query(Inject)
                    .join(Template)
                    .join(Team)
                    .filter(Team.name.in_(data["unselectedTeams"]))
                    .filter(Template.id == template.id)
                    .all()
                )
                for inject in injects:
                    inject.enabled = False
            db.session.commit()
            return jsonify({"status": "Success"}), 200
        else:
            return jsonify({"status": "Error", "message": "Missing Data"}), 400
    else:
        return {"status": "Unauthorized"}, 403


# TODO - Generate injects from templates
@mod.route("/api/admin/injects/templates/import", methods=["POST"])
@login_required
def admin_import_inject_templates():
    if current_user.is_white_team:
        data = request.get_json()
        if data:
            for d in data:
                if d.get("id"):
                    template_id = d["id"]
                    t = db.session.get(Template, int(template_id))
                    # Update template if it exists
                    if t:
                        if d.get("title"):
                            t.title = d["title"]
                        if d.get("scenario"):
                            t.scenario = d["scenario"]
                        if d.get("deliverable"):
                            t.deliverable = d["deliverable"]
                        if d.get("start_time"):
                            t.start_time = parse(d["start_time"]).astimezone(pytz.utc).replace(tzinfo=None)
                        if d.get("end_time"):
                            t.end_time = parse(d["end_time"]).astimezone(pytz.utc).replace(tzinfo=None)
                        if "category" in d:
                            t.category = d["category"] or None
                        if d.get("enabled"):
                            t.enabled = True
                        else:
                            t.enabled = False
                        # for rubric in d["rubric"]:
                        #     if rubric.get("id"):
                        #         rubric_id = rubric["id"]
                        #     r = db.session.get(Rubric, int(rubric_id))
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
                        #         db.session.add(r)
                        # Generate injects from template
                        if d.get("selectedTeams"):
                            for team_name in data["selectedTeams"]:
                                inject = (
                                    db.session.query(Inject)
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
                                    team = db.session.query(Team).filter(Team.name == team_name).first()
                                    inject = Inject(
                                        team=team,
                                        template=template,
                                    )
                                    db.session.add(inject)
                        if d.get("unselectedTeams"):
                            injects = (
                                db.session.query(Inject)
                                .join(Template)
                                .join(Team)
                                .filter(Team.name.in_(data["unselectedTeams"]))
                                .filter(Template.id == template_id)
                                .all()
                            )
                            for inject in injects:
                                inject.enabled = False

                    else:
                        # Template ID doesn't exist, fall through to create a new one
                        d.pop("id")
                if not d.get("id"):
                    # Create the template
                    t = Template(
                        title=d["title"],
                        scenario=d["scenario"],
                        deliverable=d["deliverable"],
                        start_time=parse(d["start_time"]).astimezone(pytz.utc).replace(tzinfo=None),
                        end_time=parse(d["end_time"]).astimezone(pytz.utc).replace(tzinfo=None),
                        enabled=d["enabled"],
                    )
                    db.session.add(t)
                    db.session.flush()
                    # Create rubric items (backward compat: if only "score" exists, create default item)
                    if d.get("rubric_items"):
                        for idx, item_data in enumerate(d["rubric_items"]):
                            rubric_item = RubricItem(
                                title=item_data["title"],
                                description=item_data.get("description", ""),
                                points=item_data["points"],
                                order=item_data.get("order", idx),
                                template=t,
                            )
                            db.session.add(rubric_item)
                    elif d.get("score"):
                        rubric_item = RubricItem(
                            title="Overall Quality",
                            description="",
                            points=int(d["score"]),
                            order=0,
                            template=t,
                        )
                        db.session.add(rubric_item)
                    for team_name in d["teams"]:
                        inject = (
                            db.session.query(Inject)
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
                            team = db.session.query(Team).filter(Team.name == team_name).first()
                            if team:
                                inject = Inject(
                                    team=team,
                                    template=t,
                                )
                                db.session.add(inject)
            db.session.commit()
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
            db.session.query(Inject)
            .options(joinedload(Inject.template), joinedload(Inject.team))
            .order_by(Inject.template_id)
            .order_by(Inject.team_id)
            .all()
        )

        for inject in injects:
            if inject.team is None:
                continue
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
                    "max_score": inject.template.max_score,
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
            db.session.query(Inject.team_id, func.sum(InjectRubricScore.score))
            .join(InjectRubricScore)
            .filter(Inject.status == "Graded")
            .group_by(Inject.team_id)
            .all()
        )

        team_data = {}
        team_labels = []
        team_inject_scores = []
        blue_teams = db.session.query(Team).filter(Team.color == "Blue").order_by(Team.name).all()
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
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            template = db.session.get(Template, int(request.form["pk"]))
            if template:
                modified_check = False
                if request.form["name"] == "template_state":
                    template.state = request.form["value"]
                    modified_check = True
                elif request.form["name"] == "template_points":
                    template.points = request.form["value"]
                    modified_check = True
                if modified_check:
                    db.session.add(template)
                    db.session.commit()
                    # update_scoreboard_data()
                    # update_overview_data()
                    # update_services_navbar(check.service.team.id)
                    # update_team_stats(check.service.team.id)
                    # update_services_data(check.service.team.id)
                    # update_service_data(check.service.id)
                    return jsonify({"status": "Updated Property Information"})
            return jsonify({"error": "Template Not Found"})
    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/admin/injects/ungraded")
@login_required
def admin_get_ungraded_injects():
    """Flat, cross-team list of inject submissions awaiting grading. White team only.

    "Awaiting grading" means status Submitted or Resubmitted (the per-template
    submissions endpoint only shows one template at a time). Sorted by team then
    title for a stable grading order.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    injects = (
        db.session.query(Inject)
        .options(joinedload(Inject.template), joinedload(Inject.team), joinedload(Inject.files))
        .filter(Inject.status.in_(("Submitted", "Resubmitted")))
        .all()
    )
    data = []
    for inject in injects:
        # Skip orphaned submissions with no team/template: they can't be attributed
        # or graded, and dereferencing the missing relation would 500 the whole
        # list (the scores endpoints guard the same way -- see `if inject.team`).
        if inject.team is None or inject.template is None:
            continue
        data.append(
            {
                "inject_id": inject.id,
                "team": inject.team.name,
                "title": inject.template.title,
                "status": inject.status,
                "file_count": len(inject.files),
            }
        )
    data.sort(key=lambda d: (d["team"].lower(), d["title"].lower()))
    return jsonify(data=data)


@mod.route("/api/admin/injects/download_ungraded")
@login_required
def admin_download_ungraded_injects():
    """Bundle every ungraded submission's files into one ZIP for offline grading.

    Files are laid out as ``<team>/<inject title>/<original name>`` so a grader can
    tell submissions apart at a glance; collisions inside a folder get a numeric
    suffix. White team only. 404 when nothing is awaiting grading (empty ZIP is
    not useful and would look like a success).
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    injects = (
        db.session.query(Inject)
        .options(joinedload(Inject.template), joinedload(Inject.team), joinedload(Inject.files))
        .filter(Inject.status.in_(("Submitted", "Resubmitted")))
        .all()
    )

    zip_buffer = io.BytesIO()
    files_added = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for inject in injects:
            # Orphaned submissions (no team/template) can't be laid out in the
            # archive and aren't gradeable; skip them rather than 500.
            if inject.team is None or inject.template is None:
                continue
            team_dir = secure_filename(inject.team.name) or f"team_{inject.team_id}"
            inject_dir = secure_filename(inject.template.title) or f"inject_{inject.id}"
            for f in inject.files:
                # Files are stored under upload_folder/<inject id>/<team name>/<stored name>;
                # see api_injects_file_upload.
                src = os.path.join(config.upload_folder, str(inject.id), inject.team.name, f.filename)
                if not os.path.exists(src):
                    continue
                display = secure_filename(f.original_filename or f.filename) or f.filename
                arcname = f"{team_dir}/{inject_dir}/{display}"
                candidate, counter = arcname, 1
                while candidate in zip_file.namelist():
                    root, ext = os.path.splitext(arcname)
                    candidate = f"{root}_{counter}{ext}"
                    counter += 1
                zip_file.write(src, candidate)
                files_added += 1

    if files_added == 0:
        return jsonify({"error": "No ungraded submission files found"}), 404

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="ungraded_submissions.zip",
    )


@mod.route("/api/admin/get_teams")
@login_required
def admin_get_teams():
    if current_user.is_white_team:
        all_teams = db.session.query(Team).all()
        data = []
        for team in all_teams:
            users = {}
            for user in team.users:
                users[user.username] = [user.password, str(user.authenticated).title()]
            data.append({"name": team.name, "color": team.color, "users": users})
        return jsonify(data=data)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_hosts")
@login_required
def admin_get_hosts():
    """Distinct service hosts across all teams, sorted ascending. White team only.

    Gives organizers an inventory of every host in the competition (one row per
    unique host, deduplicated across teams) without exposing per-team scoring
    detail. Read-only, so it is not cached the same way the scoreboard is -- the
    host list changes only when services are added/edited.
    """
    if current_user.is_white_team:
        hosts = db.session.query(Service.host).distinct().order_by(Service.host).all()
        return jsonify(data=[{"host": host} for (host,) in hosts])
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_password", methods=["POST"])
@login_required
def admin_update_password():
    if current_user.is_white_team:
        if "user_id" in request.form and "password" in request.form:
            try:
                user_obj = db.session.query(User).filter(User.id == request.form["user_id"]).one()
            except NoResultFound:
                return redirect(url_for("auth.login"))
            # NOTE: do NOT html.escape() the password. It is hashed, never rendered,
            # and escaping here would silently change the credential so that
            # /login (which compares the raw string) could never match it.
            user_obj.update_password(request.form["password"])
            user_obj.authenticated = False
            db.session.add(user_obj)
            db.session.commit()
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
        if "username" in request.form and "password" in request.form and "team_id" in request.form:
            team_obj = db.session.query(Team).filter(Team.id == request.form["team_id"]).one()
            # NOTE: credentials are stored verbatim (the password is hashed). Escaping
            # them here would silently change them so that /login, which compares the
            # raw submitted values, could never match. Escaping happens at render time
            # (Jinja autoescapes; JS-built markup escapes explicitly).
            user_obj = User(
                username=request.form["username"],
                password=request.form["password"],
                team=team_obj,
            )
            db.session.add(user_obj)
            db.session.commit()
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
            # NOTE: team names are stored verbatim, exactly as competition.py stores the
            # ones defined in the YAML. Escaping here would make an admin-created team
            # named "Team <1>" render as "Team &lt;1&gt;" (double-escaped, since every
            # render site escapes), and would break agent PSK derivation, which hashes
            # the raw team name. Escaping happens at render time instead.
            team_obj = Team(request.form["name"], request.form["color"])
            db.session.add(team_obj)
            db.session.commit()
            flash("Team successfully added.", "success")
            return redirect(url_for("admin.manage"))
        else:
            flash("Error: Team name or color not defined.", "danger")
            return redirect(url_for("admin.manage"))
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/toggle_inject_scores_visible", methods=["POST"])
@login_required
def admin_toggle_inject_scores_visible():
    if current_user.is_white_team:
        Setting.clear_cache("inject_scores_visible")
        setting = Setting.get_setting("inject_scores_visible")
        setting.value = not setting.value
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("inject_scores_visible")
        update_scoreboard_data()
        update_all_inject_data()
        update_overview_data()
        publish_event("settings_changed", {"setting": "inject_scores_visible"})
        return {"status": "Success"}
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/toggle_engine", methods=["POST"])
@login_required
def admin_toggle_engine():
    if current_user.is_white_team:
        Setting.clear_cache("engine_paused")
        setting = Setting.get_setting("engine_paused")
        setting.value = not setting.value
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("engine_paused")
        publish_event("settings_changed", {"setting": "engine_paused"})
        return {"status": "Success"}
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/get_engine_stats")
@login_required
def admin_get_engine_stats():
    if current_user.is_white_team:
        engine_stats = {}
        engine_stats["round_number"] = Round.get_last_round_num()
        engine_stats["num_passed_checks"] = db.session.query(Check).filter_by(result=True).count()
        engine_stats["num_failed_checks"] = db.session.query(Check).filter_by(result=False).count()
        engine_stats["total_checks"] = db.session.query(Check).count()
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


@mod.route("/api/admin/get_competition_summary")
@login_required
def admin_get_competition_summary():
    if current_user.is_white_team:
        blue_teams = db.session.query(Team).filter(Team.color == "Blue").all()
        total_services = db.session.query(Service).join(Team).filter(Team.color == "Blue").count()
        total_checks = db.session.query(Check).count()
        passed_checks = db.session.query(Check).filter_by(result=True).count()

        overall_uptime = 0.0
        if total_checks > 0:
            overall_uptime = round((passed_checks / total_checks) * 100, 1)

        last_round = Round.get_last_round_num()
        currently_passing = 0
        if last_round > 0:
            currently_passing = (
                db.session.query(Check).join(Round).filter(Round.number == last_round, Check.result == True).count()
            )

        return jsonify(
            {
                "blue_teams": len(blue_teams),
                "total_services": total_services,
                "currently_passing": currently_passing,
                "overall_uptime": overall_uptime,
            }
        )
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/welcome/config", methods=["GET"])
@login_required
def admin_get_welcome_config():
    """Get the welcome page configuration."""
    if current_user.is_white_team:
        config = get_welcome_config()
        return jsonify(data=config)
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/welcome/config", methods=["PUT"])
@login_required
def admin_update_welcome_config():
    """Update the welcome page configuration."""
    if current_user.is_white_team:
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "status": "Error",
                        "message": "No data provided",
                    }
                ),
                400,
            )

        try:
            config = save_welcome_config(data)
            return jsonify({"status": "Success", "data": config})
        except ValueError as e:
            return jsonify({"status": "Error", "message": str(e)}), 400
    else:
        return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/welcome/upload_logo", methods=["POST"])
@login_required
def admin_upload_sponsor_logo():
    """Upload a sponsor logo image."""
    import os

    from werkzeug.utils import secure_filename

    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    if "file" not in request.files:
        return (
            jsonify(
                {
                    "status": "Error",
                    "message": "No file provided",
                }
            ),
            400,
        )

    file = request.files["file"]
    if file.filename == "":
        return (
            jsonify(
                {
                    "status": "Error",
                    "message": "No file selected",
                }
            ),
            400,
        )

    # Validate file extension
    allowed = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        return (
            jsonify(
                {
                    "status": "Error",
                    "message": "File type not allowed. Use: " + ", ".join(sorted(allowed)),
                }
            ),
            400,
        )

    filename = secure_filename(file.filename)

    # Save to the shared upload folder (Docker volume), not the static dir.
    # Static files are served by nginx from a separate container/mount,
    # so uploads to the web container's static/ dir would be inaccessible.
    sponsors_dir = os.path.join(config.upload_folder, "sponsors")
    os.makedirs(sponsors_dir, exist_ok=True)

    # Avoid overwriting: add suffix if file exists
    filepath = os.path.join(sponsors_dir, filename)
    if os.path.exists(filepath):
        name, dot_ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(filepath):
            filename = f"{name}_{counter}{dot_ext}"
            filepath = os.path.join(sponsors_dir, filename)
            counter += 1

    file.save(filepath)

    url = f"/api/admin/welcome/sponsor_logo/{filename}"
    return jsonify({"status": "Success", "url": url})


@mod.route("/api/admin/welcome/sponsor_logo/<filename>")
def serve_sponsor_logo(filename):
    """Serve a sponsor logo from the upload folder."""
    import os

    from flask import abort, send_from_directory
    from werkzeug.utils import secure_filename

    safe_filename = secure_filename(filename)
    if not safe_filename:
        abort(404)
    sponsors_dir = os.path.join(config.upload_folder, "sponsors")
    return send_from_directory(sponsors_dir, safe_filename)


# Global cache for loaded check classes (loaded once per app lifecycle)
_check_classes = None


def _get_check_classes():
    """Load and cache all check classes."""
    global _check_classes
    if _check_classes is None:
        _check_classes = {}
        loaded_checks = Engine.load_check_files(config.checks_location)
        for check_class in loaded_checks:
            _check_classes[check_class.__name__] = check_class
    return _check_classes


@mod.route("/api/admin/check/dry_run", methods=["POST"])
@login_required
def admin_check_dry_run():
    """
    Run a service check without recording results to the database.
    Dispatches to a Celery worker so the check runs in an environment
    that has the required tools (SSH client, DNS utils, etc.).
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json()
    if not data or "service_id" not in data:
        return jsonify({"status": "error", "message": "service_id is required"}), 400

    service_id = data.get("service_id")
    environment_id = data.get("environment_id")

    service = db.session.get(Service, int(service_id))
    if not service:
        return jsonify({"status": "error", "message": f"Service with id {service_id} not found"}), 404

    # Get environment (specific or random)
    if environment_id:
        environment = db.session.get(Environment, int(environment_id))
        if not environment or environment.service_id != service.id:
            return jsonify({"status": "error", "message": f"Environment {environment_id} not found for service"}), 404
    else:
        if not service.environments:
            return jsonify({"status": "error", "message": "Service has no environments configured"}), 400
        import random

        environment = random.choice(service.environments)

    # Load check class and generate command
    check_classes = _get_check_classes()
    check_class = check_classes.get(service.check_name)
    if not check_class:
        return jsonify({"status": "error", "message": f"Check class '{service.check_name}' not found"}), 404

    try:
        check_obj = check_class(environment)
        command = check_obj.command()
    except LookupError as e:
        return jsonify({"status": "error", "message": f"Check configuration error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error instantiating check: {str(e)}"}), 500

    # Dispatch to a Celery worker via the service's worker queue
    import time

    job = {"command": command, "env": check_obj.command_env}
    start_time = time.time()
    try:
        result = execute_command.apply_async(args=[job], queue=service_queue(service, check_class))
        completed_job = result.get(timeout=35)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Worker execution failed: {str(e)}"}), 500
    execution_time_ms = int((time.time() - start_time) * 1000)

    # Evaluate result against matching_content
    if completed_job.get("errored_out"):
        check_result = False
        reason = CHECK_TIMED_OUT_TEXT
    else:
        output = completed_job.get("output", "")
        if re.search(environment.matching_content, output):
            check_result = True
            reason = CHECK_SUCCESS_TEXT
        else:
            check_result = False
            reason = CHECK_FAILURE_TEXT

    return jsonify(
        {
            "status": "success",
            "result": check_result,
            "reason": reason,
            "output": completed_job.get("output", "")[:35000],
            "command": command,
            "execution_time_ms": execution_time_ms,
            "service_name": service.name,
            "team_name": service.team.name,
            "host": service.host,
            "port": service.port,
            "matching_content": environment.matching_content,
            "environment_id": environment.id,
        }
    )


@mod.route("/api/admin/rollback", methods=["POST"])
@login_required
def admin_rollback():
    """
    Rollback competition data to a specific round.

    Deletes all rounds, checks, and KB entries from the specified round onwards.
    This is a destructive operation - use with caution.

    Request JSON:
    {
        "round_number": 10,  // Delete this round and all after it
        "confirm": true      // Required to confirm destructive action
    }
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Request body required"}), 400

    round_number = data.get("round_number")
    confirm = data.get("confirm", False)

    if round_number is None:
        return jsonify({"status": "error", "message": "round_number is required"}), 400

    try:
        round_number = int(round_number)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "round_number must be an integer"}), 400

    if round_number < 1:
        return jsonify({"status": "error", "message": "round_number must be >= 1"}), 400

    if not confirm:
        return jsonify({"status": "error", "message": "confirm=true required for destructive operation"}), 400

    # Get current round count for validation
    current_round = Round.get_last_round_num()
    if current_round == 0:
        return jsonify({"status": "error", "message": "No rounds exist to rollback"}), 400

    if round_number > current_round:
        return (
            jsonify(
                {"status": "error", "message": f"round_number ({round_number}) exceeds current round ({current_round})"}
            ),
            400,
        )

    # Pause the engine to prevent race conditions during rollback
    was_paused = Setting.get_setting("engine_paused").value
    if not was_paused:
        setting = Setting.get_setting("engine_paused")
        setting.value = True
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("engine_paused")
        # Wait for the engine to finish its current round and notice the pause
        time.sleep(5)

    try:
        # Revoke any pending Celery tasks for rounds being rolled back
        task_kb_entries = db.session.query(KB).filter(KB.round_num >= round_number, KB.name == "task_ids").all()
        revoked_count = 0
        for kb_entry in task_kb_entries:
            try:
                task_dict = json.loads(kb_entry.value)
                for team_name, task_id_list in task_dict.items():
                    for task_id in task_id_list:
                        execute_command.AsyncResult(task_id).revoke(terminate=True)
                        revoked_count += 1
            except (json.JSONDecodeError, TypeError):
                pass

        # Get rounds to delete
        rounds_to_delete = db.session.query(Round).filter(Round.number >= round_number).all()
        round_ids = [r.id for r in rounds_to_delete]

        # Count checks to delete
        checks_count = db.session.query(Check).filter(Check.round_id.in_(round_ids)).count()

        # Count KB entries to delete
        kb_count = db.session.query(KB).filter(KB.round_num >= round_number).count()

        # Count materialized round scores to delete
        round_scores_count = db.session.query(RoundScore).filter(RoundScore.round_number >= round_number).count()

        # Delete checks in batches to avoid lock wait timeout
        BATCH_SIZE = 500
        for i in range(0, len(round_ids), BATCH_SIZE):
            batch_ids = round_ids[i : i + BATCH_SIZE]
            db.session.query(Check).filter(Check.round_id.in_(batch_ids)).delete(synchronize_session=False)
            db.session.commit()

        # Delete materialized round scores. Keyed by round_number, so they must go
        # with the rounds or the scoreboard keeps ghost points for deleted rounds.
        db.session.query(RoundScore).filter(RoundScore.round_number >= round_number).delete(synchronize_session=False)
        db.session.commit()

        # Delete KB entries
        db.session.query(KB).filter(KB.round_num >= round_number).delete(synchronize_session=False)
        db.session.commit()

        # Delete rounds
        rounds_count = len(rounds_to_delete)
        db.session.query(Round).filter(Round.number >= round_number).delete(synchronize_session=False)
        db.session.commit()

    finally:
        # Unpause engine if we paused it (even on error)
        if not was_paused:
            Setting.clear_cache("engine_paused")
            setting = Setting.get_setting("engine_paused")
            setting.value = False
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("engine_paused")

    # Clear all caches to force recalculation
    from flask import current_app

    update_all_cache(current_app)

    return jsonify(
        {
            "status": "success",
            "message": f"Rolled back to before round {round_number}",
            "deleted": {
                "rounds": rounds_count,
                "checks": checks_count,
                "kb_entries": kb_count,
                "round_scores": round_scores_count,
            },
            "new_current_round": Round.get_last_round_num(),
        }
    )


@mod.route("/api/admin/rollback/preview", methods=["POST"])
@login_required
def admin_rollback_preview():
    """Preview what would be deleted by a rollback operation."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Request body required"}), 400

    round_number = data.get("round_number")
    if round_number is None:
        return jsonify({"status": "error", "message": "round_number is required"}), 400

    try:
        round_number = int(round_number)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "round_number must be an integer"}), 400

    if round_number < 1:
        return jsonify({"status": "error", "message": "round_number must be >= 1"}), 400

    current_round = Round.get_last_round_num()
    if current_round == 0:
        return jsonify(
            {
                "status": "success",
                "current_round": 0,
                "round_number": round_number,
                "will_delete": {"rounds": 0, "checks": 0, "kb_entries": 0, "round_scores": 0},
            }
        )

    # Get rounds that would be deleted
    rounds_to_delete = db.session.query(Round).filter(Round.number >= round_number).all()
    round_ids = [r.id for r in rounds_to_delete]

    # Count checks
    checks_count = db.session.query(Check).filter(Check.round_id.in_(round_ids)).count() if round_ids else 0

    # Count KB entries
    kb_count = db.session.query(KB).filter(KB.round_num >= round_number).count()

    # Count materialized round scores
    round_scores_count = db.session.query(RoundScore).filter(RoundScore.round_number >= round_number).count()

    return jsonify(
        {
            "status": "success",
            "current_round": current_round,
            "round_number": round_number,
            "will_delete": {
                "rounds": len(rounds_to_delete),
                "checks": checks_count,
                "kb_entries": kb_count,
                "round_scores": round_scores_count,
            },
        }
    )


@mod.route("/api/admin/adjustments", methods=["GET"])
@login_required
def admin_get_adjustments():
    """List all manual score adjustments (append-only audit log), newest first."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    rows = (
        db.session.query(ScoreAdjustment).order_by(ScoreAdjustment.created_at.desc(), ScoreAdjustment.id.desc()).all()
    )
    data = [
        {
            "id": adj.id,
            "team": adj.team.name if adj.team else None,
            "team_id": adj.team_id,
            "points": adj.points,
            "reason": adj.reason,
            "author": adj.author.username if adj.author else None,
            "created_at": ensure_utc_aware(adj.created_at).isoformat() if adj.created_at else None,
        }
        for adj in rows
    ]
    return jsonify(data=data)


@mod.route("/api/admin/adjustments", methods=["POST"])
@login_required
def admin_create_adjustment():
    """Create a manual score adjustment (bonus or penalty) for a team.

    Append-only: there is no edit or delete. To reverse an adjustment, add a
    compensating one, so the audit trail stays complete.
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json(silent=True) or request.form
    team_id = data.get("team_id")
    points = data.get("points")
    reason = (data.get("reason") or "").strip()

    if team_id is None or points is None or not reason:
        return jsonify({"status": "error", "message": "team_id, points, and reason are required"}), 400
    try:
        team_id = int(team_id)
        points = int(points)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "team_id and points must be integers"}), 400

    team = db.session.get(Team, team_id)
    if team is None:
        return jsonify({"status": "error", "message": "Team not found"}), 404

    adjustment = ScoreAdjustment(team_id=team_id, points=points, reason=reason, author_id=current_user.id)
    db.session.add(adjustment)
    db.session.commit()

    # The team's total changed; refresh the scoreboard caches.
    update_scoreboard_data()

    return (
        jsonify(
            {
                "status": "success",
                "id": adjustment.id,
                "team": team.name,
                "points": points,
                "reason": reason,
            }
        ),
        201,
    )


@mod.route("/api/admin/freeze", methods=["GET"])
@login_required
def admin_get_freeze():
    """Return the current scoreboard freeze setting (raw UTC ISO, or null)."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403
    setting = Setting.get_setting("scoreboard_freeze_time")
    value = setting.value if setting else None
    return jsonify(freeze_time=value or None)


@mod.route("/api/admin/freeze", methods=["POST"])
@login_required
def admin_set_freeze():
    """Set or clear the wall-clock scoreboard freeze.

    Accepts ``freeze_time`` as an ISO datetime. A naive value (no offset) is
    interpreted in the competition timezone (config.timezone), matching how times
    are displayed everywhere else. An empty value clears the freeze. Stored as a
    naive-UTC ISO string.
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json(silent=True) or request.form
    raw = (data.get("freeze_time") or "").strip()

    if not raw:
        value = ""
    else:
        try:
            dt = parse(raw)
        except (ValueError, TypeError, OverflowError):
            return jsonify({"status": "error", "message": "Invalid datetime"}), 400
        if dt.tzinfo is None:
            dt = pytz.timezone(config.timezone).localize(dt)
        value = dt.astimezone(pytz.utc).replace(tzinfo=None).isoformat()

    setting = Setting.get_setting("scoreboard_freeze_time")
    setting.value = value
    db.session.add(setting)
    db.session.commit()
    Setting.clear_cache("scoreboard_freeze_time")

    # Freeze changes what every non-white viewer sees; refresh the standings caches.
    update_scoreboard_data()
    update_overview_data()
    update_flags_data()

    return jsonify({"status": "success", "freeze_time": value or None})


def _parse_competition_time(raw):
    """Parse an operator-entered datetime into a naive-UTC datetime, or None.

    A naive value (no offset) is interpreted in the competition timezone
    (``config.timezone``), matching how the freeze is parsed and how times are
    displayed everywhere else. Returns None on empty or unparseable input.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        dt = parse(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = pytz.timezone(config.timezone).localize(dt)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def _refresh_after_window_change():
    """Invalidate the schedule cache and the standings caches a window affects."""
    clear_windows_cache()
    update_scoreboard_data()
    update_overview_data()
    update_flags_data()


@mod.route("/api/admin/windows", methods=["GET"])
@login_required
def admin_get_windows():
    """List competition windows (white team only), in schedule order."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403
    windows = db.session.query(CompetitionWindow).order_by(CompetitionWindow.start_time).all()
    return jsonify(windows=[w.to_dict() for w in windows])


@mod.route("/api/admin/windows", methods=["POST"])
@login_required
def admin_create_window():
    """Create a competition window.

    Accepts ``name`` (optional), ``start_time`` and ``end_time`` as ISO datetimes.
    Naive values are interpreted in the competition timezone; stored naive-UTC.
    Rejects a window whose end is not strictly after its start.
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip() or None
    start = _parse_competition_time(data.get("start_time"))
    end = _parse_competition_time(data.get("end_time"))

    if start is None or end is None:
        return jsonify({"status": "error", "message": "Valid start_time and end_time are required"}), 400
    if end <= start:
        return jsonify({"status": "error", "message": "end_time must be after start_time"}), 400

    window = CompetitionWindow(name=name, start_time=start, end_time=end, enabled=True)
    db.session.add(window)
    db.session.commit()

    _refresh_after_window_change()
    return jsonify({"status": "success", "window": window.to_dict()})


@mod.route("/api/admin/windows/<int:window_id>", methods=["PATCH"])
@login_required
def admin_toggle_window(window_id):
    """Enable/disable a window without deleting it (park a cancelled day)."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403
    window = db.session.get(CompetitionWindow, window_id)
    if window is None:
        return jsonify({"status": "error", "message": "Not found"}), 404

    data = request.get_json(silent=True) or request.form
    if "enabled" in data:
        raw = data.get("enabled")
        window.enabled = raw is True or str(raw).lower() in ("true", "1", "on", "yes")
    else:
        window.enabled = not window.enabled
    db.session.add(window)
    db.session.commit()

    _refresh_after_window_change()
    return jsonify({"status": "success", "window": window.to_dict()})


@mod.route("/api/admin/windows/<int:window_id>", methods=["DELETE"])
@login_required
def admin_delete_window(window_id):
    """Delete a competition window."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403
    window = db.session.get(CompetitionWindow, window_id)
    if window is None:
        return jsonify({"status": "error", "message": "Not found"}), 404
    db.session.delete(window)
    db.session.commit()
    _refresh_after_window_change()
    return jsonify({"status": "success"})


def _upsert_setting(name, value):
    """Set a setting, creating the row if a pre-feature DB never seeded it."""
    setting = Setting.get_setting(name)
    if setting is None:
        setting = Setting(name=name, value=value)
    else:
        setting.value = value
    db.session.add(setting)
    db.session.commit()
    Setting.clear_cache(name)


@mod.route("/api/admin/weighted_scoring", methods=["GET"])
@login_required
def admin_get_weighted_scoring():
    """Return the current weighted-scoring configuration (white team only)."""
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    def _float(name, default):
        setting = Setting.get_setting(name)
        try:
            return float(setting.value) if setting else default
        except (ValueError, TypeError):
            return default

    enabled = Setting.get_setting("weighted_scoring_enabled")
    return jsonify(
        enabled=bool(enabled.value) if enabled else False,
        service_weight=_float("service_weight", 1.0),
        inject_weight=_float("inject_weight", 1.0),
        flag_weight=_float("flag_weight", 1.0),
    )


@mod.route("/api/admin/weighted_scoring", methods=["POST"])
@login_required
def admin_set_weighted_scoring():
    """Set weighted-scoring configuration (white team only).

    Accepts ``enabled`` (bool) and ``service_weight`` / ``inject_weight`` /
    ``flag_weight`` (numbers >= 0). Absent fields are left unchanged; a present
    weight that is negative or unparseable is rejected.
    """
    if not current_user.is_white_team:
        return jsonify({"status": "Unauthorized"}), 403

    data = request.get_json(silent=True) or request.form

    if "enabled" in data:
        raw = data.get("enabled")
        _upsert_setting("weighted_scoring_enabled", raw is True or str(raw).lower() in ("true", "1", "on", "yes"))

    for name in ("service_weight", "inject_weight", "flag_weight"):
        if name in data:
            try:
                weight = float(data[name])
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": f"{name} must be a number"}), 400
            if weight < 0:
                return jsonify({"status": "error", "message": f"{name} must be >= 0"}), 400
            _upsert_setting(name, str(weight))

    # Weights change every team's combined total and the red flag total.
    update_scoreboard_data()
    update_overview_data()
    update_flags_data()
    publish_event("settings_changed", {"setting": "weighted_scoring"})

    return jsonify({"status": "success"})
