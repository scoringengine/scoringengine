from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import relationship

from datetime import datetime
import pytz

from scoring_engine.models.base import Base
from scoring_engine.config import config
from scoring_engine.db import session


class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    checks = relationship("Check", back_populates="round")
    ownership_checks = relationship('OwnershipRecord', back_populates='round')
    round_start = Column(DateTime, default=datetime.utcnow)
    round_end = Column(DateTime)

    @staticmethod
    def get_last_round_num():
        round_obj = session.query(Round).order_by(Round.number.desc()).first()
        if round_obj is None:
            return 0
        else:
            return round_obj.number

    @staticmethod
    def get_last_round():
        return session.query(Round).order_by(Round.number.desc()).first()

    @staticmethod
    def get_previous_rounds(num):
        rounds = session.query(Round).order_by(Round.number.desc()).all()
        return rounds[0:num]

    @property
    def local_round_start(self):
        round_start_obj = pytz.timezone('UTC').localize(self.round_start)
        return round_start_obj.astimezone(pytz.timezone(config.timezone)).strftime('%Y-%m-%d %H:%M:%S')
