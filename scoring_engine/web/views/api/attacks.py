"""API endpoints for attack logging and correlation with service failures."""
from datetime import timedelta

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import joinedload

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.flag import Flag, Solve, Platform, Perm
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team

from . import mod


@mod.route("/api/attacks/timeline")
@login_required
def attacks_timeline():
    """
    Get attack timeline showing flag captures with timestamps.
    Returns captures ordered by time, most recent first.

    Query params:
        limit: max results (default 100)
        team_id: filter by blue team (victim)
        host: filter by host
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    limit = request.args.get("limit", 100, type=int)
    team_id = request.args.get("team_id", type=int)
    host = request.args.get("host")

    query = (
        db.session.query(Solve)
        .options(joinedload(Solve.flag), joinedload(Solve.team))
        .join(Flag)
        .filter(Flag.dummy.is_(False))  # Exclude dummy flags
    )

    if team_id:
        # Filter by blue team - need to match host to service
        services = db.session.query(Service.host).filter(Service.team_id == team_id).all()
        hosts = [s.host for s in services]
        query = query.filter(Solve.host.in_(hosts))

    if host:
        query = query.filter(Solve.host == host)

    # Order by captured_at if available, otherwise by id (creation order)
    solves = (
        query.order_by(desc(Solve.captured_at), desc(Solve.id))
        .limit(limit)
        .all()
    )

    # Get blue team info for each host
    host_to_team = {}
    all_hosts = set(s.host for s in solves)
    if all_hosts:
        services = (
            db.session.query(Service.host, Team.id, Team.name)
            .join(Team)
            .filter(Service.host.in_(all_hosts))
            .filter(Team.color == "Blue")
            .all()
        )
        for service in services:
            host_to_team[service.host] = {"id": service.id, "name": service.name}

    data = []
    for solve in solves:
        blue_team = host_to_team.get(solve.host)
        data.append({
            "id": solve.id,
            "flag_id": solve.flag_id,
            "host": solve.host,
            "red_team": {
                "id": solve.team.id,
                "name": solve.team.name,
            } if solve.team else None,
            "blue_team": blue_team,
            "captured_at": solve.captured_at.isoformat() if solve.captured_at else None,
            "captured_at_local": solve.localize_captured_at,
            "flag": {
                "type": solve.flag.type.value,
                "platform": solve.flag.platform.value,
                "perm": solve.flag.perm.value,
            } if solve.flag else None,
        })

    return jsonify({"data": data, "count": len(data)})


@mod.route("/api/attacks/correlation")
@login_required
def attacks_correlation():
    """
    Correlate flag captures with service check failures.
    Shows which service failures occurred near the time of flag captures.

    Query params:
        window_seconds: time window around capture to look for failures (default 300 = 5 min)
        team_id: filter by blue team
        limit: max captures to analyze (default 50)
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    window_seconds = request.args.get("window_seconds", 300, type=int)
    team_id = request.args.get("team_id", type=int)
    limit = request.args.get("limit", 50, type=int)

    # Get recent captures with timestamps
    query = (
        db.session.query(Solve)
        .options(joinedload(Solve.flag), joinedload(Solve.team))
        .join(Flag)
        .filter(Flag.dummy.is_(False))
        .filter(Solve.captured_at.isnot(None))  # Only captures with timestamps
    )

    if team_id:
        services = db.session.query(Service.host).filter(Service.team_id == team_id).all()
        hosts = [s.host for s in services]
        query = query.filter(Solve.host.in_(hosts))

    solves = (
        query.order_by(desc(Solve.captured_at))
        .limit(limit)
        .all()
    )

    # Build host -> service/team mapping
    all_hosts = set(s.host for s in solves)
    host_to_service = {}
    if all_hosts:
        services = (
            db.session.query(Service)
            .options(joinedload(Service.team))
            .filter(Service.host.in_(all_hosts))
            .all()
        )
        for service in services:
            if service.host not in host_to_service:
                host_to_service[service.host] = []
            host_to_service[service.host].append(service)

    correlations = []
    for solve in solves:
        capture_time = solve.captured_at
        window_start = capture_time - timedelta(seconds=window_seconds)
        window_end = capture_time + timedelta(seconds=window_seconds)

        # Find services on this host
        services_on_host = host_to_service.get(solve.host, [])

        # Find failed checks in the time window for services on this host
        related_failures = []
        for service in services_on_host:
            failed_checks = (
                db.session.query(Check)
                .join(Round)
                .filter(Check.service_id == service.id)
                .filter(Check.result.is_(False))
                .filter(Check.completed_timestamp.isnot(None))
                .filter(Check.completed_timestamp >= window_start)
                .filter(Check.completed_timestamp <= window_end)
                .order_by(Check.completed_timestamp)
                .all()
            )

            for check in failed_checks:
                # Calculate time difference from capture
                time_diff = (check.completed_timestamp - capture_time).total_seconds()
                related_failures.append({
                    "check_id": check.id,
                    "service_id": service.id,
                    "service_name": service.name,
                    "team_id": service.team_id,
                    "team_name": service.team.name if service.team else None,
                    "check_time": check.completed_timestamp.isoformat() if check.completed_timestamp else None,
                    "reason": check.reason,
                    "seconds_from_capture": int(time_diff),
                    "before_or_after": "before" if time_diff < 0 else "after",
                })

        correlations.append({
            "capture": {
                "id": solve.id,
                "flag_id": solve.flag_id,
                "host": solve.host,
                "captured_at": capture_time.isoformat(),
                "red_team": solve.team.name if solve.team else None,
                "flag_type": solve.flag.type.value if solve.flag else None,
                "flag_platform": solve.flag.platform.value if solve.flag else None,
                "flag_perm": solve.flag.perm.value if solve.flag else None,
            },
            "related_failures": related_failures,
            "failure_count": len(related_failures),
            "likely_caused_by_attack": len([f for f in related_failures if f["seconds_from_capture"] >= 0]) > 0,
        })

    # Summary statistics
    total_captures = len(correlations)
    captures_with_failures = len([c for c in correlations if c["failure_count"] > 0])
    likely_attack_caused = len([c for c in correlations if c["likely_caused_by_attack"]])

    return jsonify({
        "correlations": correlations,
        "summary": {
            "total_captures": total_captures,
            "captures_with_nearby_failures": captures_with_failures,
            "likely_attack_caused_failures": likely_attack_caused,
            "window_seconds": window_seconds,
        },
    })


@mod.route("/api/attacks/summary")
@login_required
def attacks_summary():
    """
    Get summary statistics of attack activity.
    Shows capture counts by team, platform, permission level, and time.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    # Total captures (excluding dummy flags)
    total_captures = (
        db.session.query(func.count(Solve.id))
        .join(Flag)
        .filter(Flag.dummy.is_(False))
        .scalar()
    )

    # Captures by red team
    captures_by_red_team = (
        db.session.query(Team.name, func.count(Solve.id).label("count"))
        .join(Solve, Solve.team_id == Team.id)
        .join(Flag, Solve.flag_id == Flag.id)
        .filter(Flag.dummy.is_(False))
        .group_by(Team.id, Team.name)
        .order_by(desc("count"))
        .all()
    )

    # Captures by platform
    captures_by_platform = (
        db.session.query(Flag.platform, func.count(Solve.id).label("count"))
        .join(Solve)
        .filter(Flag.dummy.is_(False))
        .group_by(Flag.platform)
        .all()
    )

    # Captures by permission level
    captures_by_perm = (
        db.session.query(Flag.perm, func.count(Solve.id).label("count"))
        .join(Solve)
        .filter(Flag.dummy.is_(False))
        .group_by(Flag.perm)
        .all()
    )

    # Build host -> blue team mapping for victim stats
    all_hosts = [r[0] for r in db.session.query(Solve.host).distinct().all()]
    host_to_team = {}
    if all_hosts:
        services = (
            db.session.query(Service.host, Team.id, Team.name)
            .join(Team)
            .filter(Service.host.in_(all_hosts))
            .filter(Team.color == "Blue")
            .distinct()
            .all()
        )
        for service in services:
            host_to_team[service.host] = {"id": service.id, "name": service.name}

    # Captures targeting each blue team (victim stats)
    solves_with_hosts = (
        db.session.query(Solve.host)
        .join(Flag)
        .filter(Flag.dummy.is_(False))
        .all()
    )

    victims = {}
    for (host,) in solves_with_hosts:
        team_info = host_to_team.get(host)
        if team_info:
            team_name = team_info["name"]
            victims[team_name] = victims.get(team_name, 0) + 1

    captures_by_victim = sorted(victims.items(), key=lambda x: -x[1])

    return jsonify({
        "total_captures": total_captures,
        "by_red_team": [{"team": t, "count": c} for t, c in captures_by_red_team],
        "by_platform": [{"platform": p.value if p else "unknown", "count": c} for p, c in captures_by_platform],
        "by_permission": [{"perm": p.value if p else "unknown", "count": c} for p, c in captures_by_perm],
        "by_victim": [{"team": t, "count": c} for t, c in captures_by_victim],
    })


@mod.route("/api/attacks/service/<int:service_id>/history")
@login_required
def attacks_service_history(service_id):
    """
    Get attack history for a specific service.
    Shows captures and check failures together in timeline.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    # Get captures on this host
    captures = (
        db.session.query(Solve)
        .options(joinedload(Solve.flag), joinedload(Solve.team))
        .join(Flag)
        .filter(Flag.dummy.is_(False))
        .filter(Solve.host == service.host)
        .order_by(desc(Solve.captured_at))
        .limit(100)
        .all()
    )

    # Get recent check failures for this service
    failures = (
        db.session.query(Check)
        .join(Round)
        .filter(Check.service_id == service_id)
        .filter(Check.result.is_(False))
        .order_by(desc(Check.completed_timestamp))
        .limit(100)
        .all()
    )

    # Build combined timeline
    timeline = []

    for capture in captures:
        timeline.append({
            "type": "capture",
            "timestamp": capture.captured_at.isoformat() if capture.captured_at else None,
            "data": {
                "id": capture.id,
                "flag_id": capture.flag_id,
                "red_team": capture.team.name if capture.team else None,
                "platform": capture.flag.platform.value if capture.flag else None,
                "perm": capture.flag.perm.value if capture.flag else None,
            },
        })

    for check in failures:
        timeline.append({
            "type": "failure",
            "timestamp": check.completed_timestamp.isoformat() if check.completed_timestamp else None,
            "data": {
                "check_id": check.id,
                "round": check.round.number if check.round else None,
                "reason": check.reason,
            },
        })

    # Sort by timestamp (None values at end)
    timeline.sort(key=lambda x: x["timestamp"] or "9999", reverse=True)

    return jsonify({
        "service": {
            "id": service.id,
            "name": service.name,
            "host": service.host,
            "team": service.team.name if service.team else None,
        },
        "timeline": timeline[:100],
        "total_captures": len(captures),
        "total_failures": len(failures),
    })
