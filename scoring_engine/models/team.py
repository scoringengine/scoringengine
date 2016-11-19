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
        sorted_blue_teams = sorted(self.blue_teams, key=lambda team: team.current_score, reverse=True)
        place = 0
        for index, team in enumerate(sorted_blue_teams):
            if self.id == team.id:
                place = index + 1
        return place

    @property
    def is_red_team(self):
        return self.color == 'Red'

    @property
    def is_white_team(self):
        return self.color == 'White'

    @property
    def is_blue_team(self):
        return self.color == 'Blue'

    @property
    def blue_teams(self):
        return Team.query.filter(Team.color == 'Blue').all()
