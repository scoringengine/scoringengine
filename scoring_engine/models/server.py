from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="servers")
    services = relationship("Service", back_populates="server")
