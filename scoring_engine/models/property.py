from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    environment_id = Column(Integer, ForeignKey("environments.id"))
    environment = relationship("Environment")
    visible = Column(Boolean, default=False)
