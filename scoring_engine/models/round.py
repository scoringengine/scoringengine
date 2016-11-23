from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    checks = relationship("Check", back_populates="round")

    @staticmethod
    def get_last_round_num():
        round_obj = Round.query.order_by(Round.number.desc()).first()
        if round_obj is None:
            return 0
        else:
            return round_obj.number
