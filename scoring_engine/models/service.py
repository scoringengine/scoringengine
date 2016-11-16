from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    check_name = Column(String(50), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="services")
    properties = relationship("Property", back_populates="service")
    checks = relationship("Check", back_populates="service")

    def last_check_result(self):
        return self.checks[-1].result
