import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UnicodeText,
)
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(UnicodeText, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Audience targeting
    # Values: 'global', 'all_blue', 'all_red', 'team:5', 'teams:1,3,5'
    audience = Column(String(255), nullable=False, default="global")

    is_pinned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    author = relationship("User", foreign_keys=[author_id])

    def __init__(self, title, content, audience="global", author_id=None):
        self.title = title
        self.content = content
        self.audience = audience
        self.author_id = author_id

    def is_visible_to_user(self, user):
        """
        Check if this announcement is visible to a given user.
        Returns True if the announcement should be shown to this user.
        """
        # Check if announcement is active
        if not self.is_active:
            return False

        # Check if announcement has expired
        if self.expires_at and _utcnow() > self.expires_at:
            return False

        # Global announcements are visible to everyone
        if self.audience == "global":
            return True

        # If no user is logged in, only global announcements are visible
        if user is None:
            return False
        if not hasattr(user, "is_authenticated") or not user.is_authenticated:
            return False

        # White team can see all announcements
        if user.is_white_team:
            return True

        # all_blue - visible to all blue teams
        if self.audience == "all_blue":
            return user.is_blue_team

        # all_red - visible to red team only
        if self.audience == "all_red":
            return user.is_red_team

        # team:ID - visible to specific team by ID
        if self.audience.startswith("team:"):
            try:
                team_id = int(self.audience.split(":")[1])
                return user.team.id == team_id
            except (ValueError, IndexError, AttributeError):
                return False

        # teams:1,3,5 - visible to multiple specific teams
        if self.audience.startswith("teams:"):
            try:
                team_ids_str = self.audience.split(":")[1]
                team_ids = [int(x.strip()) for x in team_ids_str.split(",")]
                return user.team.id in team_ids
            except (ValueError, IndexError, AttributeError):
                return False

        return False

    def to_dict(self):
        """Convert announcement to dictionary for JSON serialization."""
        created = self.created_at.isoformat() if self.created_at else None
        expires = self.expires_at.isoformat() if self.expires_at else None
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": created,
            "author_id": self.author_id,
            "author_name": self.author.username if self.author else None,
            "audience": self.audience,
            "is_pinned": self.is_pinned,
            "is_active": self.is_active,
            "expires_at": expires,
        }


