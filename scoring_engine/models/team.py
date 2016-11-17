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

    def __init__(self, name, color):
        self.name = name
        self.color = color

    @property
    def current_score(self):
        total_score = 0
        for service in self.services:
            total_score += service.score_earned
        return total_score

    @property
    def place(self):
        # todo make this dynamic
        return 2

    @property
    def is_red_team(self):
        return self.color == 'Red'

    @property
    def is_white_team(self):
        return self.color == 'White'

    @property
    def is_blue_team(self):
        return self.color == 'Blue'
