from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class OwnershipRecord(Base):
    __tablename__ = 'ownership_records'
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    round = relationship('Round', back_populates='ownership_checks')
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship('Service')
    owning_team_id = Column(Integer, ForeignKey('teams.id'))
    owning_team = relationship('Team')
