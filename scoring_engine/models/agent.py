import enum
import html
import uuid

import pytz
from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer,
                        PickleType, String, UniqueConstraint)
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from scoring_engine.cache import cache
from scoring_engine.config import config
from scoring_engine.models.base import Base
from scoring_engine.models.flag import FlagTypeEnum, Platform
from scoring_engine.models.team import Team


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
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
