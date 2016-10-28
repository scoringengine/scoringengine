from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class Check(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    round = relationship("Round", back_populates="checks")
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship("Service")
