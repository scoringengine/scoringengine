from sqlalchemy import Column, Integer, ForeignKey, Text, String
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(Text, nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship("Service")
