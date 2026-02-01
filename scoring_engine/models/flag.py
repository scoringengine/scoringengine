import html

import pytz
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, PickleType, String, UniqueConstraint, func

# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return pytz.utc.localize(dt)
    # Already aware - convert to UTC
    return dt.astimezone(pytz.utc)


import enum
import uuid

from scoring_engine.config import config
from scoring_engine.models.base import Base
from scoring_engine.models.team import Team


class FlagTypeEnum(enum.Enum):
    file = "file"
    pipe = "pipe"
    net = "net"
    reg = "reg"


class Platform(enum.Enum):
    windows = "win"
    nix = "nix"


class Perm(enum.Enum):
    user = "user"
    root = "root"


class Flag(Base):
    __tablename__ = "flags"
    # id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(FlagTypeEnum), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    data = Column(PickleType, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    perm = Column(Enum(Perm), nullable=False)
    dummy = Column(Boolean, nullable=False, default=False)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "platform": self.platform.value,
            "start_time": int(_ensure_utc_aware(self.start_time).timestamp()),
            "end_time": int(_ensure_utc_aware(self.end_time).timestamp()),
            "perm": self.perm.value,
            "dummy": self.dummy,
        }

    @property
    def localize_start_time(self):
        return (
            _ensure_utc_aware(self.start_time)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @property
    def localize_end_time(self):
        return (
            _ensure_utc_aware(self.end_time).astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")
        )


class Solve(Base):
    __tablename__ = "flag_solves"
    __table_args__ = (UniqueConstraint("flag_id", "host", "team_id", name="_flag_host_team_uc"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(260), nullable=False)
    flag_id = Column(String(36), ForeignKey("flags.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    captured_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)
    flag = relationship("Flag", backref="solves", lazy="joined")
    team = relationship("Team", backref="flag_solves", lazy="joined")

    @property
    def localize_captured_at(self):
        """Get captured_at timestamp in configured timezone."""
        if self.captured_at is None:
            return None
        return (
            _ensure_utc_aware(self.captured_at)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )


class PersistenceSession(Base):
    """
    Tracks a red team persistence session on a blue team host.

    A session starts when the agent first checks in from a compromised host
    and ends when:
    - The agent stops checking in (timeout - blue team remediated)
    - Manually marked as ended by admin
    """

    __tablename__ = "persistence_sessions"
    __table_args__ = (UniqueConstraint("host", "team_id", "ended_at", name="_host_team_active_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(260), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_checkin = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)  # Null = still active

    # End reason
    end_reason = Column(String(50), nullable=True)  # timeout, manual, competition_end

    # Relationships
    team = relationship("Team", backref="persistence_sessions")

    @property
    def is_active(self):
        """Check if this session is still active."""
        return self.ended_at is None

    @property
    def duration_seconds(self):
        """Calculate session duration in seconds."""
        from datetime import datetime, timezone

        if self.ended_at is None:
            end = datetime.now(timezone.utc)
        else:
            end = _ensure_utc_aware(self.ended_at)
        start = _ensure_utc_aware(self.started_at)
        return int((end - start).total_seconds())

    @property
    def duration_formatted(self):
        """Get human-readable duration."""
        seconds = self.duration_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @property
    def localize_started_at(self):
        """Get started_at in configured timezone."""
        return (
            _ensure_utc_aware(self.started_at)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @property
    def localize_last_checkin(self):
        """Get last_checkin in configured timezone."""
        return (
            _ensure_utc_aware(self.last_checkin)
            .astimezone(pytz.timezone(config.timezone))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @property
    def localize_ended_at(self):
        """Get ended_at in configured timezone."""
        if self.ended_at is None:
            return None
        return (
            _ensure_utc_aware(self.ended_at).astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")
        )
