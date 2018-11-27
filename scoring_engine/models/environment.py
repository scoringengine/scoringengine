from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Environment(Base):
    __tablename__ = "environments"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship("Service")
    properties = relationship('Property', back_populates="environment")
    matching_content = Column(Text, nullable=False)
