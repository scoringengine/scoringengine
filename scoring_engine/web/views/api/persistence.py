"""API endpoints for tracking red team persistence on compromised hosts."""
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import joinedload

from scoring_engine.db import db
from scoring_engine.models.flag import PersistenceSession, Platform
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team

from . import mod


def get_persistence_timeout_seconds():
    """Get the persistence timeout from settings, defaulting to 5 minutes."""
    try:
        timeout = Setting.get_setting("persistence_timeout_seconds")
        return int(timeout.value) if timeout else 300
    except Exception:
        return 300  # 5 minutes default


@mod.route("/api/persistence/sessions")
@login_required
def persistence_sessions():
    """
    Get all persistence sessions.

    Query params:
        active_only: if 'true', only show active sessions
        team_id: filter by blue team (victim)
        limit: max results (default 100)
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    active_only = request.args.get("active_only", "false").lower() == "true"
    team_id = request.args.get("team_id", type=int)
    limit = request.args.get("limit", 100, type=int)

    query = (
        db.session.query(PersistenceSession)
        .options(joinedload(PersistenceSession.team))
    )

    if active_only:
        query = query.filter(PersistenceSession.ended_at.is_(None))

    if team_id:
        query = query.filter(PersistenceSession.team_id == team_id)

    sessions = (
        query.order_by(desc(PersistenceSession.last_checkin))
        .limit(limit)
        .all()
    )

    timeout_seconds = get_persistence_timeout_seconds()
    now = datetime.now(timezone.utc)

    data = []
    for session in sessions:
        # Check if session is stale (no recent checkin)
        last_checkin_utc = session.last_checkin
        if last_checkin_utc.tzinfo is None:
            last_checkin_utc = last_checkin_utc.replace(tzinfo=timezone.utc)

        seconds_since_checkin = (now - last_checkin_utc).total_seconds()
        is_stale = session.is_active and seconds_since_checkin > timeout_seconds

        data.append({
            "id": session.id,
            "host": session.host,
            "team_id": session.team_id,
            "team_name": session.team.name if session.team else None,
            "platform": session.platform.value if session.platform else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "started_at_local": session.localize_started_at,
            "last_checkin": session.last_checkin.isoformat() if session.last_checkin else None,
            "last_checkin_local": session.localize_last_checkin,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "ended_at_local": session.localize_ended_at,
            "end_reason": session.end_reason,
            "is_active": session.is_active,
            "is_stale": is_stale,
            "seconds_since_checkin": int(seconds_since_checkin),
            "duration_seconds": session.duration_seconds,
            "duration_formatted": session.duration_formatted,
        })

    return jsonify({
        "data": data,
        "count": len(data),
        "timeout_seconds": timeout_seconds,
    })


@mod.route("/api/persistence/active")
@login_required
def persistence_active():
    """
    Get currently active persistence sessions.
    Convenience endpoint that filters to active sessions only.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    timeout_seconds = get_persistence_timeout_seconds()
    now = datetime.now(timezone.utc)
    timeout_threshold = now - timedelta(seconds=timeout_seconds)

    # Active sessions with recent checkin
    sessions = (
        db.session.query(PersistenceSession)
        .options(joinedload(PersistenceSession.team))
        .filter(PersistenceSession.ended_at.is_(None))
        .filter(PersistenceSession.last_checkin >= timeout_threshold.replace(tzinfo=None))
        .order_by(desc(PersistenceSession.last_checkin))
        .all()
    )

    data = []
    for session in sessions:
        last_checkin_utc = session.last_checkin
        if last_checkin_utc.tzinfo is None:
            last_checkin_utc = last_checkin_utc.replace(tzinfo=timezone.utc)

        data.append({
            "id": session.id,
            "host": session.host,
            "team_id": session.team_id,
            "team_name": session.team.name if session.team else None,
            "platform": session.platform.value if session.platform else None,
            "started_at_local": session.localize_started_at,
            "last_checkin_local": session.localize_last_checkin,
            "duration_formatted": session.duration_formatted,
            "seconds_since_checkin": int((now - last_checkin_utc).total_seconds()),
        })

    return jsonify({
        "data": data,
        "count": len(data),
        "timeout_seconds": timeout_seconds,
    })


@mod.route("/api/persistence/detect_stale", methods=["POST"])
@login_required
def persistence_detect_stale():
    """
    Detect and end stale persistence sessions.
    Sessions that haven't checked in within the timeout are marked as ended.

    Returns the number of sessions that were ended.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    timeout_seconds = get_persistence_timeout_seconds()
    now = datetime.now(timezone.utc)
    timeout_threshold = now - timedelta(seconds=timeout_seconds)

    # Find stale active sessions
    stale_sessions = (
        db.session.query(PersistenceSession)
        .filter(PersistenceSession.ended_at.is_(None))
        .filter(PersistenceSession.last_checkin < timeout_threshold.replace(tzinfo=None))
        .all()
    )

    ended_count = 0
    for session in stale_sessions:
        session.ended_at = session.last_checkin  # End time is last known checkin
        session.end_reason = "timeout"
        ended_count += 1

    db.session.commit()

    return jsonify({
        "status": "success",
        "sessions_ended": ended_count,
        "timeout_seconds": timeout_seconds,
    })


@mod.route("/api/persistence/session/<int:session_id>/end", methods=["POST"])
@login_required
def persistence_end_session(session_id):
    """Manually end a persistence session."""
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    session = db.session.get(PersistenceSession, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.ended_at:
        return jsonify({"error": "Session already ended"}), 400

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.ended_at = now
    session.end_reason = "manual"
    db.session.commit()

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "duration_seconds": session.duration_seconds,
        "duration_formatted": session.duration_formatted,
    })


@mod.route("/api/persistence/summary")
@login_required
def persistence_summary():
    """
    Get persistence summary statistics.
    Shows total persistence time by team, active sessions, etc.
    """
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    timeout_seconds = get_persistence_timeout_seconds()
    now = datetime.now(timezone.utc)
    timeout_threshold = now - timedelta(seconds=timeout_seconds)

    # Total sessions
    total_sessions = db.session.query(func.count(PersistenceSession.id)).scalar()

    # Active sessions (not ended and recently checked in)
    active_sessions = (
        db.session.query(func.count(PersistenceSession.id))
        .filter(PersistenceSession.ended_at.is_(None))
        .filter(PersistenceSession.last_checkin >= timeout_threshold.replace(tzinfo=None))
        .scalar()
    )

    # Stale sessions (not ended but no recent checkin)
    stale_sessions = (
        db.session.query(func.count(PersistenceSession.id))
        .filter(PersistenceSession.ended_at.is_(None))
        .filter(PersistenceSession.last_checkin < timeout_threshold.replace(tzinfo=None))
        .scalar()
    )

    # Ended sessions
    ended_sessions = (
        db.session.query(func.count(PersistenceSession.id))
        .filter(PersistenceSession.ended_at.isnot(None))
        .scalar()
    )

    # Sessions by team (victim)
    sessions_by_team = (
        db.session.query(
            Team.name,
            func.count(PersistenceSession.id).label("count"),
        )
        .join(PersistenceSession, PersistenceSession.team_id == Team.id)
        .group_by(Team.id, Team.name)
        .order_by(desc("count"))
        .all()
    )

    # Active sessions by team
    active_by_team = (
        db.session.query(
            Team.name,
            func.count(PersistenceSession.id).label("count"),
        )
        .join(PersistenceSession, PersistenceSession.team_id == Team.id)
        .filter(PersistenceSession.ended_at.is_(None))
        .filter(PersistenceSession.last_checkin >= timeout_threshold.replace(tzinfo=None))
        .group_by(Team.id, Team.name)
        .order_by(desc("count"))
        .all()
    )

    # Sessions by platform
    sessions_by_platform = (
        db.session.query(
            PersistenceSession.platform,
            func.count(PersistenceSession.id).label("count"),
        )
        .group_by(PersistenceSession.platform)
        .all()
    )

    # Calculate average persistence duration for ended sessions
    ended = (
        db.session.query(PersistenceSession)
        .filter(PersistenceSession.ended_at.isnot(None))
        .all()
    )
    total_duration = sum(s.duration_seconds for s in ended)
    avg_duration = total_duration // len(ended) if ended else 0

    # Longest persistence session
    longest_session = None
    all_sessions = db.session.query(PersistenceSession).all()
    if all_sessions:
        longest = max(all_sessions, key=lambda s: s.duration_seconds)
        longest_session = {
            "id": longest.id,
            "host": longest.host,
            "team_name": longest.team.name if longest.team else None,
            "duration_formatted": longest.duration_formatted,
            "duration_seconds": longest.duration_seconds,
        }

    return jsonify({
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "stale_sessions": stale_sessions,
        "ended_sessions": ended_sessions,
        "by_team": [{"team": t, "count": c} for t, c in sessions_by_team],
        "active_by_team": [{"team": t, "count": c} for t, c in active_by_team],
        "by_platform": [
            {"platform": p.value if p else "unknown", "count": c}
            for p, c in sessions_by_platform
        ],
        "average_duration_seconds": avg_duration,
        "average_duration_formatted": format_duration(avg_duration),
        "longest_session": longest_session,
        "timeout_seconds": timeout_seconds,
    })


@mod.route("/api/persistence/team/<int:team_id>")
@login_required
def persistence_by_team(team_id):
    """Get persistence history for a specific team."""
    if not current_user.is_white_team:
        return {"status": "Unauthorized"}, 403

    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404

    sessions = (
        db.session.query(PersistenceSession)
        .filter(PersistenceSession.team_id == team_id)
        .order_by(desc(PersistenceSession.started_at))
        .all()
    )

    timeout_seconds = get_persistence_timeout_seconds()
    now = datetime.now(timezone.utc)

    # Calculate total persistence time
    total_duration = sum(s.duration_seconds for s in sessions)

    # Active sessions count
    active_count = sum(1 for s in sessions if s.is_active)

    # Unique hosts compromised
    unique_hosts = len(set(s.host for s in sessions))

    data = []
    for session in sessions:
        last_checkin_utc = session.last_checkin
        if last_checkin_utc.tzinfo is None:
            last_checkin_utc = last_checkin_utc.replace(tzinfo=timezone.utc)

        seconds_since_checkin = (now - last_checkin_utc).total_seconds()
        is_stale = session.is_active and seconds_since_checkin > timeout_seconds

        data.append({
            "id": session.id,
            "host": session.host,
            "platform": session.platform.value if session.platform else None,
            "started_at_local": session.localize_started_at,
            "last_checkin_local": session.localize_last_checkin,
            "ended_at_local": session.localize_ended_at,
            "end_reason": session.end_reason,
            "is_active": session.is_active,
            "is_stale": is_stale,
            "duration_formatted": session.duration_formatted,
        })

    return jsonify({
        "team_id": team_id,
        "team_name": team.name,
        "sessions": data,
        "total_sessions": len(sessions),
        "active_sessions": active_count,
        "unique_hosts": unique_hosts,
        "total_duration_seconds": total_duration,
        "total_duration_formatted": format_duration(total_duration),
    })


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


# =============================================================================
# External C2 Beacon Integration (Cobalt Strike, etc.)
# =============================================================================

@mod.route("/api/persistence/beacon", methods=["POST"])
def persistence_beacon():
    """
    External C2 beacon check-in endpoint.

    Allows external C2 frameworks (Cobalt Strike, Mythic, etc.) to report
    their beacons to the persistence tracking system via webhook/API.

    Authentication: PSK in Authorization header
        Authorization: Bearer <persistence_beacon_psk>

    Request body (JSON):
        {
            "team": "Team 1",           # Blue team name (victim)
            "host": "webserver.local",  # Compromised host
            "platform": "win" | "nix",  # Platform (win/nix)
            "beacon_id": "abc123",      # Optional: external beacon ID
            "user": "DOMAIN\\user",     # Optional: compromised user
            "metadata": {}              # Optional: additional metadata
        }

    Returns:
        {
            "status": "success",
            "session_id": 123,
            "action": "created" | "updated"
        }
    """
    # Check if beacon PSK is configured
    psk_setting = Setting.get_setting("persistence_beacon_psk")
    if not psk_setting or not psk_setting.value:
        return jsonify({"error": "Beacon API not configured"}), 503

    # Validate PSK
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    provided_psk = auth_header[7:]  # Remove "Bearer " prefix
    if provided_psk != psk_setting.value:
        return jsonify({"error": "Invalid PSK"}), 401

    # Parse request body
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    team_name = data.get("team")
    host = data.get("host")
    platform_str = data.get("platform")

    if not team_name or not host or not platform_str:
        return jsonify({"error": "Missing required fields: team, host, platform"}), 400

    # Validate platform
    try:
        platform = Platform(platform_str)
    except ValueError:
        return jsonify({"error": f"Invalid platform: {platform_str}. Use 'win' or 'nix'"}), 400

    # Find team
    team = db.session.query(Team).filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": f"Team not found: {team_name}"}), 404

    if not team.is_blue_team:
        return jsonify({"error": "Target must be a blue team"}), 400

    # Include optional metadata in host identifier for beacon tracking
    beacon_id = data.get("beacon_id")
    if beacon_id:
        # Use beacon_id in host to track individual beacons separately
        host = f"{host}:{beacon_id}"

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Find or create session
    active_session = (
        db.session.query(PersistenceSession)
        .filter(
            and_(
                PersistenceSession.host == host,
                PersistenceSession.team_id == team.id,
                PersistenceSession.ended_at.is_(None),
            )
        )
        .first()
    )

    if active_session:
        # Update existing session
        active_session.last_checkin = now
        active_session.platform = platform
        action = "updated"
        session_id = active_session.id
    else:
        # Create new session
        session = PersistenceSession(
            host=host,
            team_id=team.id,
            platform=platform,
            started_at=now,
            last_checkin=now,
        )
        db.session.add(session)
        db.session.flush()  # Get ID before commit
        action = "created"
        session_id = session.id

    db.session.commit()

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "action": action,
        "host": host,
        "team": team_name,
    })


@mod.route("/api/persistence/beacon/end", methods=["POST"])
def persistence_beacon_end():
    """
    End a beacon session from external C2.

    Use when a beacon exits cleanly or is killed.

    Authentication: PSK in Authorization header

    Request body (JSON):
        {
            "team": "Team 1",
            "host": "webserver.local",
            "beacon_id": "abc123",      # Optional
            "reason": "exit"            # Optional: exit, killed, lost
        }
    """
    # Check if beacon PSK is configured
    psk_setting = Setting.get_setting("persistence_beacon_psk")
    if not psk_setting or not psk_setting.value:
        return jsonify({"error": "Beacon API not configured"}), 503

    # Validate PSK
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    provided_psk = auth_header[7:]
    if provided_psk != psk_setting.value:
        return jsonify({"error": "Invalid PSK"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    team_name = data.get("team")
    host = data.get("host")
    beacon_id = data.get("beacon_id")
    reason = data.get("reason", "external")

    if not team_name or not host:
        return jsonify({"error": "Missing required fields: team, host"}), 400

    # Find team
    team = db.session.query(Team).filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": f"Team not found: {team_name}"}), 404

    # Construct host with beacon_id if provided
    if beacon_id:
        host = f"{host}:{beacon_id}"

    # Find active session
    active_session = (
        db.session.query(PersistenceSession)
        .filter(
            and_(
                PersistenceSession.host == host,
                PersistenceSession.team_id == team.id,
                PersistenceSession.ended_at.is_(None),
            )
        )
        .first()
    )

    if not active_session:
        return jsonify({"error": "No active session found"}), 404

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    active_session.ended_at = now
    active_session.end_reason = reason
    db.session.commit()

    return jsonify({
        "status": "success",
        "session_id": active_session.id,
        "duration_seconds": active_session.duration_seconds,
        "duration_formatted": active_session.duration_formatted,
    })
