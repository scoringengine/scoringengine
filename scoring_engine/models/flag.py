from sqlalchemy import (
    Column,
    Enum,
    Integer,
    Boolean,
    PickleType,
    DateTime,
    String,
    UniqueConstraint,
    ForeignKey,
)

# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import pytz

import html


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return pytz.utc.localize(dt)
    # Already aware - convert to UTC
    return dt.astimezone(pytz.utc)

import uuid

from scoring_engine.models.base import Base
from scoring_engine.models.team import Team
from scoring_engine.config import config


import enum


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
        return _ensure_utc_aware(self.start_time).astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")

    @property
    def localize_end_time(self):
        return _ensure_utc_aware(self.end_time).astimezone(pytz.timezone(config.timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")


class Solve(Base):
    __tablename__ = "flag_solves"
    __table_args__ = (UniqueConstraint("flag_id", "host", "team_id", name="_flag_host_team_uc"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(260), nullable=False)
    flag_id = Column(String(36), ForeignKey("flags.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    flag = relationship("Flag", backref="solves", lazy="joined")
    team = relationship("Team", backref="flag_solves", lazy="joined")
