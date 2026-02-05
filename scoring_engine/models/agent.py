import enum
import html
import uuid

import pytz
from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer,
                        PickleType, String, UniqueConstraint)


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return pytz.utc.localize(dt)
    # Already aware - convert to UTC
    return dt.astimezone(pytz.utc)
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
            "start_time": int(_ensure_utc_aware(self.start_time).timestamp()),
            "end_time": int(_ensure_utc_aware(self.end_time).timestamp()),
        }
