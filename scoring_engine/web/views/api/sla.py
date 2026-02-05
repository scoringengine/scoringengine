"""
SLA API endpoints for managing SLA penalties and dynamic scoring settings.
"""

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from scoring_engine.cache_helper import (update_overview_data,
                                         update_scoreboard_data)
from scoring_engine.db import db
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.sla import (calculate_round_multiplier,
                                get_dynamic_scoring_info, get_sla_config,
                                get_team_sla_summary)

from . import mod

# ============================================================================
# SLA Summary Endpoints (Public for authenticated users)
# ============================================================================


@mod.route("/api/sla/summary")
@login_required
def sla_summary():
    """Get SLA summary for all blue teams."""
    config = get_sla_config()
    blue_teams = Team.get_all_blue_teams()

    teams_summary = []
    for team in blue_teams:
        summary = get_team_sla_summary(team, config)
        teams_summary.append(summary)

    return jsonify(
        {
            "sla_enabled": config.sla_enabled,
            "penalty_threshold": config.penalty_threshold,
            "penalty_mode": config.penalty_mode,
            "teams": teams_summary,
        }
    )


@mod.route("/api/sla/team/<int:team_id>")
@login_required
def sla_team_detail(team_id):
    """Get detailed SLA information for a specific team."""
    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404

    # Only allow white team or the team itself to view details
    if not current_user.is_white_team and current_user.team_id != team_id:
        return jsonify({"error": "Unauthorized"}), 403

    config = get_sla_config()
    summary = get_team_sla_summary(team, config)

    return jsonify(summary)


@mod.route("/api/sla/config")
@login_required
def sla_config():
    """Get current SLA configuration (admin only)."""
    if not current_user.is_white_team:
        return jsonify({"error": "Unauthorized"}), 403

    config = get_sla_config()
    return jsonify(
        {
            "sla_enabled": config.sla_enabled,
            "penalty_threshold": config.penalty_threshold,
            "penalty_percent": config.penalty_percent,
            "penalty_max_percent": config.penalty_max_percent,
            "penalty_mode": config.penalty_mode,
            "allow_negative": config.allow_negative,
        }
    )


@mod.route("/api/sla/dynamic-scoring")
@login_required
def dynamic_scoring_info():
    """Get current dynamic scoring configuration."""
    config = get_sla_config()
    info = get_dynamic_scoring_info(config)

    # Add current round multiplier and phase
    from scoring_engine.models.round import Round

    current_round = Round.get_last_round_num()
    info["current_round"] = current_round
    info["current_multiplier"] = calculate_round_multiplier(current_round, config)

    # Determine current phase based on round number
    if current_round <= config.early_rounds:
        info["current_phase"] = "early"
    elif current_round >= config.late_start_round:
        info["current_phase"] = "late"
    else:
        info["current_phase"] = "normal"

    return jsonify(info)


# ============================================================================
# Admin API Endpoints for SLA Settings
# ============================================================================


def _update_setting(name, value, redirect_route="admin.sla"):
    """Helper to update a setting value."""
    setting = Setting.get_setting(name)
    if setting:
        setting.value = value
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache(name)
        # Clear Flask cache for scoreboard/overview when SLA-related settings change
        _clear_scoring_cache()
    return redirect(url_for(redirect_route))


def _clear_scoring_cache():
    """Clear Flask cache for scoreboard and overview data."""
    update_scoreboard_data()
    update_overview_data()


@mod.route("/api/admin/update_sla_enabled", methods=["POST"])
@login_required
def admin_update_sla_enabled():
    if current_user.is_white_team:
        setting = Setting.get_setting("sla_enabled")
        if setting:
            # Toggle the value
            current_val = setting.value
            if isinstance(current_val, bool):
                setting.value = not current_val
            else:
                setting.value = str(current_val).lower() not in ("true", "1", "yes")
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("sla_enabled")
            _clear_scoring_cache()
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_sla_penalty_threshold", methods=["POST"])
@login_required
def admin_update_sla_penalty_threshold():
    if current_user.is_white_team:
        if "sla_penalty_threshold" in request.form:
            value = request.form["sla_penalty_threshold"]
            if not value.isdigit() or int(value) < 1:
                flash("Error: Penalty threshold must be a positive integer.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("sla_penalty_threshold", value)
        flash("Error: sla_penalty_threshold not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_sla_penalty_percent", methods=["POST"])
@login_required
def admin_update_sla_penalty_percent():
    if current_user.is_white_team:
        if "sla_penalty_percent" in request.form:
            value = request.form["sla_penalty_percent"]
            if not value.isdigit() or int(value) < 1:
                flash("Error: Penalty percent must be a positive integer.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("sla_penalty_percent", value)
        flash("Error: sla_penalty_percent not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_sla_penalty_max_percent", methods=["POST"])
@login_required
def admin_update_sla_penalty_max_percent():
    if current_user.is_white_team:
        if "sla_penalty_max_percent" in request.form:
            value = request.form["sla_penalty_max_percent"]
            if not value.isdigit() or int(value) < 1:
                flash(
                    "Error: Max penalty percent must be a positive integer.", "danger"
                )
                return redirect(url_for("admin.sla"))
            return _update_setting("sla_penalty_max_percent", value)
        flash("Error: sla_penalty_max_percent not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_sla_penalty_mode", methods=["POST"])
@login_required
def admin_update_sla_penalty_mode():
    if current_user.is_white_team:
        if "sla_penalty_mode" in request.form:
            value = request.form["sla_penalty_mode"]
            valid_modes = ["additive", "flat", "exponential", "next_check_reduction"]
            if value not in valid_modes:
                flash(
                    f"Error: Penalty mode must be one of: {', '.join(valid_modes)}",
                    "danger",
                )
                return redirect(url_for("admin.sla"))
            return _update_setting("sla_penalty_mode", value)
        flash("Error: sla_penalty_mode not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_sla_allow_negative", methods=["POST"])
@login_required
def admin_update_sla_allow_negative():
    if current_user.is_white_team:
        setting = Setting.get_setting("sla_allow_negative")
        if setting:
            current_val = setting.value
            if isinstance(current_val, bool):
                setting.value = not current_val
            else:
                setting.value = str(current_val).lower() not in ("true", "1", "yes")
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("sla_allow_negative")
            _clear_scoring_cache()
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


# ============================================================================
# Admin API Endpoints for Dynamic Scoring Settings
# ============================================================================


@mod.route("/api/admin/update_dynamic_scoring_enabled", methods=["POST"])
@login_required
def admin_update_dynamic_scoring_enabled():
    if current_user.is_white_team:
        setting = Setting.get_setting("dynamic_scoring_enabled")
        if setting:
            current_val = setting.value
            if isinstance(current_val, bool):
                setting.value = not current_val
            else:
                setting.value = str(current_val).lower() not in ("true", "1", "yes")
            db.session.add(setting)
            db.session.commit()
            Setting.clear_cache("dynamic_scoring_enabled")
            _clear_scoring_cache()
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_dynamic_scoring_early_rounds", methods=["POST"])
@login_required
def admin_update_dynamic_scoring_early_rounds():
    if current_user.is_white_team:
        if "dynamic_scoring_early_rounds" in request.form:
            value = request.form["dynamic_scoring_early_rounds"]
            if not value.isdigit() or int(value) < 1:
                flash("Error: Early rounds must be a positive integer.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("dynamic_scoring_early_rounds", value)
        flash("Error: dynamic_scoring_early_rounds not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_dynamic_scoring_early_multiplier", methods=["POST"])
@login_required
def admin_update_dynamic_scoring_early_multiplier():
    if current_user.is_white_team:
        if "dynamic_scoring_early_multiplier" in request.form:
            value = request.form["dynamic_scoring_early_multiplier"]
            try:
                float_val = float(value)
                if float_val <= 0:
                    raise ValueError("Must be positive")
            except ValueError:
                flash("Error: Early multiplier must be a positive number.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("dynamic_scoring_early_multiplier", value)
        flash("Error: dynamic_scoring_early_multiplier not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_dynamic_scoring_late_start_round", methods=["POST"])
@login_required
def admin_update_dynamic_scoring_late_start_round():
    if current_user.is_white_team:
        if "dynamic_scoring_late_start_round" in request.form:
            value = request.form["dynamic_scoring_late_start_round"]
            if not value.isdigit() or int(value) < 1:
                flash("Error: Late start round must be a positive integer.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("dynamic_scoring_late_start_round", value)
        flash("Error: dynamic_scoring_late_start_round not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403


@mod.route("/api/admin/update_dynamic_scoring_late_multiplier", methods=["POST"])
@login_required
def admin_update_dynamic_scoring_late_multiplier():
    if current_user.is_white_team:
        if "dynamic_scoring_late_multiplier" in request.form:
            value = request.form["dynamic_scoring_late_multiplier"]
            try:
                float_val = float(value)
                if float_val <= 0:
                    raise ValueError("Must be positive")
            except ValueError:
                flash("Error: Late multiplier must be a positive number.", "danger")
                return redirect(url_for("admin.sla"))
            return _update_setting("dynamic_scoring_late_multiplier", value)
        flash("Error: dynamic_scoring_late_multiplier not specified.", "danger")
        return redirect(url_for("admin.sla"))
    return {"status": "Unauthorized"}, 403
