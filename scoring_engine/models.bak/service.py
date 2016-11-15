from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    check_name = Column(String(50), nullable=False)
    server_id = Column(Integer, ForeignKey('servers.id'))
    server = relationship("Server", back_populates="services")
    properties = relationship("Property", back_populates="service")
    checks = relationship("Check", back_populates="service")
