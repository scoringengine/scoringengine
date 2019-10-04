from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Score(Base):
    """A team's total score at the end of a specific round."""

    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="scores", lazy="joined")
    round_id = Column(Integer, ForeignKey("rounds.id"))
    round = relationship("Round", back_populates="scores", lazy="joined")
