from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(50), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="users")
