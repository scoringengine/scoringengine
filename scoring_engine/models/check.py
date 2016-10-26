from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class Check(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True)
    round_num = Column(Integer, nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'))
    service = relationship("Service")
