import datetime

from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, UnicodeText
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    message = Column(UnicodeText)
    target = Column(UnicodeText)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Foreign Keys
    team_id = Column(Integer, ForeignKey("teams.id"))
