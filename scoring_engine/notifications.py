"""Helper functions for creating inject-related notifications with deduplication."""

from datetime import datetime, timedelta, timezone

from scoring_engine.db import db
from scoring_engine.models.notifications import Notification


def create_notification(team_id, message, target, dedup_minutes=5):
    """Create a notification with deduplication.

    If an identical notification (same team, message, target) was created
    within the last `dedup_minutes` minutes, skip creating a duplicate.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=dedup_minutes)
    existing = (
        db.session.query(Notification)
        .filter(
            Notification.team_id == team_id,
            Notification.message == message,
            Notification.target == target,
            Notification.created >= cutoff,
        )
        .first()
    )
    if existing:
        return existing

    notification = Notification(message=message, target=target)
    notification.team_id = team_id
    db.session.add(notification)
    db.session.commit()
    return notification


def notify_inject_submitted(inject):
    """Notify white team that an inject was submitted."""
    from scoring_engine.models.team import Team

    white_teams = db.session.query(Team).filter(Team.color == "White").all()
    for white_team in white_teams:
        create_notification(
            team_id=white_team.id,
            message=f"{inject.team.name} submitted inject: {inject.template.title}",
            target=f"/admin/injects/{inject.id}",
        )


def notify_inject_graded(inject):
    """Notify blue team that their inject was graded."""
    create_notification(
        team_id=inject.team_id,
        message=f"Inject graded: {inject.template.title} ({inject.score}/{inject.template.max_score})",
        target=f"/inject/{inject.id}",
    )


def notify_revision_requested(inject):
    """Notify blue team that a revision was requested."""
    create_notification(
        team_id=inject.team_id,
        message=f"Revision requested for inject: {inject.template.title}",
        target=f"/inject/{inject.id}",
    )


def notify_inject_comment(inject, commenter):
    """Notify the other party about a new comment on an inject."""
    from scoring_engine.models.team import Team

    if commenter.is_white_team:
        # White team commented -> notify the blue team
        create_notification(
            team_id=inject.team_id,
            message=f"New comment on inject: {inject.template.title}",
            target=f"/inject/{inject.id}",
        )
    else:
        # Blue team commented -> notify white team
        white_teams = db.session.query(Team).filter(Team.color == "White").all()
        for white_team in white_teams:
            create_notification(
                team_id=white_team.id,
                message=f"New comment on inject: {inject.template.title} ({inject.team.name})",
                target=f"/admin/injects/{inject.id}",
            )
