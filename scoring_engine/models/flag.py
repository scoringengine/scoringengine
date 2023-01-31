from sqlalchemy import (
    Column,
    Enum,
    Integer,
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


class Flag(Base):
    __tablename__ = "flags"
    # id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    type = Column(Enum(FlagTypeEnum), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    data = Column(PickleType, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "start_time": int(self.start_time.astimezone(pytz.utc).timestamp()),
            "end_time": int(self.end_time.astimezone(pytz.utc).timestamp()),
        }


class Solve(Base):
    __tablename__ = "flag_solves"
    __table_args__ = (
        UniqueConstraint("flag_id", "host", "team_id", name="_flag_host_team_uc"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(260), nullable=False)
    flag_id = Column(Integer, ForeignKey("flags.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    flag = relationship("Flag", backref="solves", lazy="joined")
    team = relationship("Team", backref="flag_solves", lazy="joined")
