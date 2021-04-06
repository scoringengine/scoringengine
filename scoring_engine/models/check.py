from sqlalchemy import Column, Integer, ForeignKey, Boolean, Text, DateTime, UnicodeText
from sqlalchemy.orm import relationship

from datetime import datetime
import pytz

import html

from scoring_engine.models.base import Base
from scoring_engine.config import config


class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    round = relationship('Round', back_populates='checks')
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship('Service')
    result = Column(Boolean)
    output = Column(UnicodeText, default="")
    reason = Column(Text, default="")
    command = Column(Text, default="")
    completed_timestamp = Column(DateTime)
    completed = Column(Boolean, default=False)

    def finished(self, result, reason, output, command):
        self.result = result
        self.reason = reason
        self.output = html.escape(output)
        self.completed = True
        self.completed_timestamp = datetime.utcnow()
        self.command = command

    @property
    def local_completed_timestamp(self):
        completed_timezone_obj = pytz.timezone('UTC').localize(self.completed_timestamp)
        return completed_timezone_obj.astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z')
