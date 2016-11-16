from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(String(50), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship("Service")
