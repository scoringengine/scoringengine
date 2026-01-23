"""
SLA Penalty and Dynamic Scoring Module

This module provides SLA (Service Level Agreement) penalty calculations and
dynamic scoring multipliers for the scoring engine.

Features:
- Consecutive failure penalties: Apply penalties when services fail consecutively
- Time-based scoring: Apply multipliers based on competition round/phase
- Multiple penalty modes: additive, flat, exponential, next_check_reduction
"""

from sqlalchemy import desc

from scoring_engine.db import db
from scoring_engine.models.setting import Setting


class SLAConfig:
    """Configuration holder for SLA settings loaded from database."""

    def __init__(self):
        self._load_settings()

    def _load_settings(self):
        """Load SLA settings from database."""
        self.sla_enabled = self._get_bool_setting("sla_enabled", False)
        self.penalty_threshold = self._get_int_setting("sla_penalty_threshold", 5)
        self.penalty_percent = self._get_int_setting("sla_penalty_percent", 10)
        self.penalty_max_percent = self._get_int_setting("sla_penalty_max_percent", 50)
        self.penalty_mode = self._get_string_setting("sla_penalty_mode", "additive")
        self.allow_negative = self._get_bool_setting("sla_allow_negative", False)

        # Dynamic scoring settings
        self.dynamic_enabled = self._get_bool_setting("dynamic_scoring_enabled", False)
        self.early_rounds = self._get_int_setting("dynamic_scoring_early_rounds", 10)
        self.early_multiplier = self._get_float_setting(
            "dynamic_scoring_early_multiplier", 2.0
        )
        self.late_start_round = self._get_int_setting(
            "dynamic_scoring_late_start_round", 50
        )
        self.late_multiplier = self._get_float_setting(
            "dynamic_scoring_late_multiplier", 0.5
        )

    def _get_setting(self, name, default):
        """Get a setting value from the database."""
        setting = Setting.get_setting(name)
        if setting:
            return setting.value
        return default

    def _get_bool_setting(self, name, default):
        """Get a boolean setting."""
        value = self._get_setting(name, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)

    def _get_int_setting(self, name, default):
        """Get an integer setting."""
        value = self._get_setting(name, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _get_float_setting(self, name, default):
        """Get a float setting."""
        value = self._get_setting(name, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _get_string_setting(self, name, default):
        """Get a string setting."""
        value = self._get_setting(name, default)
        return str(value) if value else default


def get_sla_config():
    """Get the current SLA configuration from the database."""
    return SLAConfig()


def get_consecutive_failures(service_id):
    """
    Count consecutive failures for a service from the most recent check going backwards.

    Returns the number of consecutive failed checks starting from the most recent.
    If the most recent check passed, returns 0.
    """
    from scoring_engine.models.check import Check

    # Query only the result column, ordered by round (most recent first)
    # Use == True instead of .is_(True) for SQLite compatibility
    checks = (
        db.session.query(Check.result)
        .filter(Check.service_id == service_id)
        .filter(Check.completed == True)  # noqa: E712
        .order_by(desc(Check.round_id))
        .all()
    )

    consecutive_failures = 0
    for (result,) in checks:
        if not result:
            consecutive_failures += 1
        else:
            # Stop counting when we hit a successful check
            break

    return consecutive_failures


def get_max_consecutive_failures(service_id):
    """
    Find the maximum streak of consecutive failures for a service across all checks.

    This is useful for historical analysis.
    """
    from scoring_engine.models.check import Check

    # Only fetch the result column, not entire Check objects
    # Use == True instead of .is_(True) for SQLite compatibility
    checks = (
        db.session.query(Check.result)
        .filter(Check.service_id == service_id)
        .filter(Check.completed == True)  # noqa: E712
        .order_by(Check.round_id)
        .all()
    )

    max_streak = 0
    current_streak = 0

    for (result,) in checks:
        if not result:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_sla_penalty_percent(consecutive_failures, config=None):
    """
    Calculate the penalty percentage based on consecutive failures and penalty mode.

    Args:
        consecutive_failures: Number of consecutive failed checks
        config: SLAConfig object (if None, loads from database)

    Returns:
        Penalty percentage (0-100 or higher if allow_negative)
    """
    if config is None:
        config = get_sla_config()

    if not config.sla_enabled:
        return 0

    if consecutive_failures < config.penalty_threshold:
        return 0

    failures_over_threshold = consecutive_failures - config.penalty_threshold

    if config.penalty_mode == "additive":
        # Linear penalty: 10%, 20%, 30%... per failure over threshold
        penalty = (failures_over_threshold + 1) * config.penalty_percent

    elif config.penalty_mode == "flat":
        # Flat penalty: Fixed percentage per failure over threshold
        penalty = failures_over_threshold * config.penalty_percent

    elif config.penalty_mode == "exponential":
        # Exponential penalty: Doubles each failure (5%, 10%, 20%, 40%...)
        penalty = config.penalty_percent * (2**failures_over_threshold)

    elif config.penalty_mode == "next_check_reduction":
        # Next check reduction mode: The service's score for next successful check
        # is reduced. This is handled separately in score calculation.
        penalty = min(
            (failures_over_threshold + 1) * config.penalty_percent,
            config.penalty_max_percent,
        )

    else:
        # Default to additive
        penalty = (failures_over_threshold + 1) * config.penalty_percent

    # Cap at max penalty unless negative scores allowed
    if not config.allow_negative:
        penalty = min(penalty, config.penalty_max_percent)

    return penalty


def calculate_round_multiplier(round_number, config=None):
    """
    Calculate the scoring multiplier for a given round based on dynamic scoring settings.

    Args:
        round_number: The round number
        config: SLAConfig object (if None, loads from database)

    Returns:
        Multiplier to apply to scores (e.g., 2.0 for double points)
    """
    if config is None:
        config = get_sla_config()

    if not config.dynamic_enabled:
        return 1.0

    if round_number <= config.early_rounds:
        return config.early_multiplier
    elif round_number >= config.late_start_round:
        return config.late_multiplier
    else:
        # Normal phase
        return 1.0


def calculate_service_base_score_with_dynamic(service, config=None):
    """
    Calculate the service's base score with dynamic scoring multipliers applied.

    Args:
        service: Service object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Base score with dynamic multipliers applied per round

    Performance: Uses a single JOIN query instead of multiple queries.
    Critical for high-traffic scenarios during competitions.
    """
    if config is None:
        config = get_sla_config()

    if not config.dynamic_enabled:
        return service.score_earned

    from scoring_engine.models.check import Check
    from scoring_engine.models.round import Round

    # Single JOIN query to get passing checks with round numbers
    # This avoids the N+1 query problem and reduces database load
    passing_checks_with_rounds = (
        db.session.query(Round.number)
        .join(Check, Check.round_id == Round.id)
        .filter(Check.service_id == service.id)
        .filter(Check.result.is_(True))
        .all()
    )

    if not passing_checks_with_rounds:
        return 0

    # Calculate total with multipliers
    # Pre-fetch config values to avoid repeated attribute access in loop
    total_score = 0
    service_points = service.points
    early_rounds = config.early_rounds
    early_multiplier = config.early_multiplier
    late_start = config.late_start_round
    late_multiplier = config.late_multiplier

    for (round_number,) in passing_checks_with_rounds:
        # Inline multiplier calculation for performance
        if round_number <= early_rounds:
            multiplier = early_multiplier
        elif round_number >= late_start:
            multiplier = late_multiplier
        else:
            multiplier = 1.0
        total_score += int(service_points * multiplier)

    return total_score


def calculate_service_penalty_points(service, config=None):
    """
    Calculate the total penalty points to deduct from a service's score.

    Args:
        service: Service object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Total penalty points to deduct
    """
    if config is None:
        config = get_sla_config()

    if not config.sla_enabled:
        return 0

    consecutive_failures = get_consecutive_failures(service.id)
    penalty_percent = calculate_sla_penalty_percent(consecutive_failures, config)

    if penalty_percent == 0:
        return 0

    # Calculate penalty based on the service's dynamic score (potential max score)
    base_score = calculate_service_base_score_with_dynamic(service, config)
    penalty_points = int(base_score * (penalty_percent / 100))

    return penalty_points


def calculate_service_adjusted_score(service, config=None):
    """
    Calculate the adjusted score for a service after applying SLA penalties.

    Args:
        service: Service object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Adjusted score after penalties
    """
    if config is None:
        config = get_sla_config()

    base_score = calculate_service_base_score_with_dynamic(service, config)
    penalty_points = calculate_service_penalty_points(service, config)

    adjusted_score = base_score - penalty_points

    if not config.allow_negative:
        adjusted_score = max(0, adjusted_score)

    return adjusted_score


def calculate_team_total_penalties(team, config=None):
    """
    Calculate the total SLA penalties for a team across all services.

    Args:
        team: Team object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Total penalty points for the team
    """
    if config is None:
        config = get_sla_config()

    if not config.sla_enabled:
        return 0

    total_penalties = 0
    for service in team.services:
        total_penalties += calculate_service_penalty_points(service, config)

    return total_penalties


def calculate_team_base_score_with_dynamic(team, config=None):
    """
    Calculate the team's base score with dynamic scoring multipliers applied.

    Args:
        team: Team object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Base score with dynamic multipliers applied per round

    Performance: Uses a single JOIN query with GROUP BY to aggregate scores
    per round, avoiding N+1 queries. Only fetches rounds with passing checks.
    Critical for high-traffic scenarios during competitions.
    """
    if config is None:
        config = get_sla_config()

    if not config.dynamic_enabled:
        return team.current_score

    from sqlalchemy.sql import func

    from scoring_engine.models.check import Check
    from scoring_engine.models.round import Round
    from scoring_engine.models.service import Service

    # Single query with JOIN to get round scores with round numbers
    # Previously queried ALL rounds which was very inefficient
    round_scores = (
        db.session.query(
            Round.number,
            func.sum(Service.points).label("round_score"),
        )
        .select_from(Check)
        .join(Service, Check.service_id == Service.id)
        .join(Round, Check.round_id == Round.id)
        .filter(Service.team_id == team.id)
        .filter(Check.result.is_(True))
        .group_by(Round.number)
        .all()
    )

    # Calculate total with multipliers
    # Pre-fetch config values to avoid repeated attribute access in loop
    total_score = 0
    early_rounds = config.early_rounds
    early_multiplier = config.early_multiplier
    late_start = config.late_start_round
    late_multiplier = config.late_multiplier

    for round_number, round_score in round_scores:
        # Inline multiplier calculation for performance
        if round_number <= early_rounds:
            multiplier = early_multiplier
        elif round_number >= late_start:
            multiplier = late_multiplier
        else:
            multiplier = 1.0
        total_score += int(round_score * multiplier)

    return total_score


def calculate_team_adjusted_score(team, config=None):
    """
    Calculate the adjusted score for a team after applying SLA penalties.

    Args:
        team: Team object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Adjusted total score after penalties
    """
    if config is None:
        config = get_sla_config()

    base_score = calculate_team_base_score_with_dynamic(team, config)
    total_penalties = calculate_team_total_penalties(team, config)

    adjusted_score = base_score - total_penalties

    if not config.allow_negative:
        adjusted_score = max(0, adjusted_score)

    return adjusted_score


def get_service_sla_status(service, config=None):
    """
    Get the SLA status for a service including consecutive failures and penalties.

    Args:
        service: Service object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Dict with SLA status information
    """
    if config is None:
        config = get_sla_config()

    consecutive_failures = get_consecutive_failures(service.id)
    penalty_percent = calculate_sla_penalty_percent(consecutive_failures, config)
    penalty_points = calculate_service_penalty_points(service, config)

    return {
        "service_id": service.id,
        "service_name": service.name,
        "consecutive_failures": consecutive_failures,
        "penalty_threshold": config.penalty_threshold,
        "penalty_percent": penalty_percent,
        "penalty_points": penalty_points,
        "base_score": calculate_service_base_score_with_dynamic(service, config),
        "adjusted_score": calculate_service_adjusted_score(service, config),
        "sla_violation": consecutive_failures >= config.penalty_threshold,
    }


def get_team_sla_summary(team, config=None):
    """
    Get a summary of SLA status for all services of a team.

    Args:
        team: Team object
        config: SLAConfig object (if None, loads from database)

    Returns:
        Dict with team SLA summary
    """
    if config is None:
        config = get_sla_config()

    services_status = []
    total_violations = 0

    for service in team.services:
        status = get_service_sla_status(service, config)
        services_status.append(status)
        if status["sla_violation"]:
            total_violations += 1

    return {
        "team_id": team.id,
        "team_name": team.name,
        "sla_enabled": config.sla_enabled,
        "base_score": calculate_team_base_score_with_dynamic(team, config),
        "total_penalties": calculate_team_total_penalties(team, config),
        "adjusted_score": calculate_team_adjusted_score(team, config),
        "services_with_violations": total_violations,
        "total_services": len(team.services),
        "services": services_status,
    }


def apply_dynamic_scoring_to_round(round_number, base_points, config=None):
    """
    Apply dynamic scoring multiplier to points for a specific round.

    Args:
        round_number: The round number
        base_points: The base points before multiplier
        config: SLAConfig object (if None, loads from database)

    Returns:
        Adjusted points after applying multiplier
    """
    if config is None:
        config = get_sla_config()

    multiplier = calculate_round_multiplier(round_number, config)
    return int(base_points * multiplier)


def get_dynamic_scoring_info(config=None):
    """
    Get information about dynamic scoring configuration.

    Args:
        config: SLAConfig object (if None, loads from database)

    Returns:
        Dict with dynamic scoring configuration
    """
    if config is None:
        config = get_sla_config()

    return {
        "enabled": config.dynamic_enabled,
        "early_rounds": config.early_rounds,
        "early_multiplier": config.early_multiplier,
        "normal_multiplier": 1.0,
        "late_start_round": config.late_start_round,
        "late_multiplier": config.late_multiplier,
        "phases": [
            {
                "name": "Early Phase",
                "rounds": f"1-{config.early_rounds}",
                "multiplier": config.early_multiplier,
            },
            {
                "name": "Normal Phase",
                "rounds": f"{config.early_rounds + 1}-{config.late_start_round - 1}",
                "multiplier": 1.0,
            },
            {
                "name": "Late Phase",
                "rounds": f"{config.late_start_round}+",
                "multiplier": config.late_multiplier,
            },
        ],
    }
