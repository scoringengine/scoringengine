from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    round = relationship('Round')
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship('Team')
    score = Column(Integer, default=0)
