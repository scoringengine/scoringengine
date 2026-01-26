from flask import request, jsonify
from flask_login import current_user, login_required
import re

import html

from scoring_engine.cache import cache
from scoring_engine.db import db
from scoring_engine.cache_helper import (
    update_overview_data,
    update_services_data,
    update_service_data,
)
from scoring_engine.models.account import Account
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.sla import get_sla_config, calculate_round_multiplier, calculate_sla_penalty_percent

from . import make_cache_key, mod


def is_valid_user_input(string, only_alphanumberdot, only_number):
    if only_alphanumberdot:
        regex = r"^[A-Za-z0-9.]+$"
    elif only_number:
        regex = r"^[0-9]+$"
    else:
        regex = r"^[A-Za-z0-9\.,@=:\/\-\|\(\); !]+$"
        if string.startswith(" ") or string.endswith(" "):
            return False
    return bool(re.match(regex, string))


@mod.route("/api/service/<service_id>/checks")
@login_required
@cache.cached(make_cache_key=make_cache_key)
def service_get_checks(service_id):
    service = db.session.get(Service, service_id)
    if service is None or not (current_user.team == service.team or current_user.team.is_white_team):
        return jsonify({"status": "Unauthorized"}), 403

    # Query checks ordered by round number ascending for penalty calculation
    check_output = (
        db.session.query(Check, Round.number)
        .join(Round)
        .filter(Check.service_id == service_id)
        .order_by(Round.number.asc())
        .all()
    )

    # Get SLA config for dynamic scoring and penalties
    sla_config = get_sla_config()
    service_points = service.points
    sla_enabled = sla_config.sla_enabled

    # Process checks in chronological order to track consecutive failures
    data = []
    consecutive_failures = 0

    for check, round_number in check_output:
        # Calculate the round multiplier
        multiplier = calculate_round_multiplier(round_number, sla_config)

        # Calculate earned score for this check
        if check.result:
            # Base earned score with multiplier
            base_earned = int(service_points * multiplier)

            # Apply SLA penalty based on consecutive failures at this point
            if sla_enabled and consecutive_failures > 0:
                penalty_percent = calculate_sla_penalty_percent(consecutive_failures, sla_config)
                earned_score = int(base_earned * (100 - penalty_percent) / 100)
                sla_penalty_applied = penalty_percent
            else:
                earned_score = base_earned
                sla_penalty_applied = 0

            # Reset consecutive failures after a pass
            consecutive_failures = 0
        else:
            earned_score = 0
            sla_penalty_applied = 0
            consecutive_failures += 1

        data.append({
            "id": check.id,
            "round": round_number,
            "result": check.result,
            "earned_score": earned_score,
            "multiplier": multiplier,
            "sla_penalty": sla_penalty_applied,
            "timestamp": check.local_completed_timestamp,
            "reason": check.reason,
            "output": check.output,
            "command": check.command,
        })

    # Reverse to show most recent first (descending order)
    data.reverse()

    if Setting.get_setting("blue_team_view_check_output").value is False and current_user.is_blue_team:
        for check in data:
            check["output"] = "REDACTED"
    return jsonify(data=data)


@mod.route("/api/service/update_account", methods=["POST"])
@login_required
def update_service_account_info():
    if current_user.is_white_team or current_user.is_blue_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            if is_valid_user_input(request.form["value"], False, False):
                if request.form["name"] == "username":
                    modify_usernames_setting = Setting.get_setting("blue_team_update_account_usernames")
                    if modify_usernames_setting.value is False and current_user.is_blue_team:
                        return jsonify({"error": "Incorrect permissions"})

                elif request.form["name"] == "password":
                    modify_passwords_setting = Setting.get_setting("blue_team_update_account_passwords")
                    if modify_passwords_setting.value is False and current_user.is_blue_team:
                        return jsonify({"error": "Incorrect permissions"})

                account = db.session.query(Account).get(int(request.form["pk"]))
                if account:
                    if current_user.team == account.service.team or current_user.is_white_team:
                        if request.form["name"] == "username":
                            account.username = html.escape(request.form["value"])
                        elif request.form["name"] == "password":
                            account.password = html.escape(request.form["value"])
                        db.session.add(account)
                        db.session.commit()
                        return jsonify({"status": "Updated Account Information"})
            else:
                return jsonify({"error": "Invalid input characters detected"})

    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/service/update_host", methods=["POST"])
@login_required
def update_host():
    if current_user.is_white_team or current_user.is_blue_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            if is_valid_user_input(request.form["value"], True, False):
                modify_hostname_setting = Setting.get_setting("blue_team_update_hostname")
                if modify_hostname_setting.value is False and current_user.is_blue_team:
                    return jsonify({"error": "Incorrect permissions"})

                service = db.session.query(Service).get(int(request.form["pk"]))
                if service:
                    if (service.team == current_user.team or current_user.is_white_team) and request.form["name"] == "host":
                        service.host = html.escape(request.form["value"])
                        db.session.add(service)
                        db.session.commit()
                        update_overview_data()
                        update_services_data(service.team.id)
                        update_service_data(service.id)
                        return jsonify({"status": "Updated Service Information"})
            else:
                return jsonify({"error": "Invalid input characters detected"})

    return jsonify({"error": "Incorrect permissions"})


@mod.route("/api/service/update_port", methods=["POST"])
@login_required
def update_port():
    if current_user.is_white_team or current_user.is_blue_team:
        if "name" in request.form and "value" in request.form and "pk" in request.form:
            if is_valid_user_input(request.form["value"], False, True):
                modify_port_setting = Setting.get_setting("blue_team_update_port")
                if modify_port_setting.value is False and current_user.is_blue_team:
                    return jsonify({"error": "Incorrect permissions"})

                service = db.session.query(Service).get(int(request.form["pk"]))
                if service:
                    if (service.team == current_user.team or current_user.is_white_team) and request.form["name"] == "port":
                        service.port = int(html.escape(request.form["value"]))
                        db.session.add(service)
                        db.session.commit()
                        update_overview_data()
                        update_services_data(service.team.id)
                        update_service_data(service.id)
                        return jsonify({"status": "Updated Service Information"})
            else:
                return jsonify({"error": "Invalid input characters detected"})

    return jsonify({"error": "Incorrect permissions"})
