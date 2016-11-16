from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    color = Column(String(10), nullable=False)
    services = relationship("Service", back_populates="team")
    users = relationship("User", back_populates="team")

    def current_score(self):
        # todo make this dynamic based on service result
        return 2000
