from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import relationship

from datetime import datetime, timezone
import pytz

from scoring_engine.models.base import Base
from scoring_engine.config import config
from scoring_engine.db import db


def _ensure_utc_aware(dt):
    """Ensure datetime is timezone-aware in UTC. Handles both naive and aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return pytz.utc.localize(dt)
    # Already aware - convert to UTC
    return dt.astimezone(pytz.utc)


class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    checks = relationship("Check", back_populates="round")
    round_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    round_end = Column(DateTime)

    @staticmethod
    def get_last_round_num():
        round_obj = db.session.query(Round.number).order_by(Round.number.desc()).first()
        if round_obj is None:
            return 0
        else:
            return round_obj.number

    @property
    def local_round_start(self):
        return _ensure_utc_aware(self.round_start).astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z')
