import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UnicodeText
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    message = Column(UnicodeText)
    target = Column(UnicodeText)
    created = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    is_read = Column(Boolean, default=False)

    # Foreign Keys
    team_id = Column(Integer, ForeignKey("teams.id"))
