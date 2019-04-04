import pytz

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime

from scoring_engine.models.base import Base
from scoring_engine.config import config


class Pwnboard(Base):
    __tablename__ = 'pwnboard'
    id = Column(Integer, primary_key=True)
    agent = Column(String(20))
    source_address = Column(String(40))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User')
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship('Service')
    timestamp = Column(DateTime)

    def __init__(self, user, service, source_address, agent=None):
        self.user = user
        self.service = service
        self.source_address = source_address
        self.agent = agent
        self.timestamp = datetime.utcnow()

    @property
    def local_timestamp(self):
        timezone_obj = pytz.timezone('UTC').localize(self.timestamp)
        return timezone_obj.astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S')
