from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from scoring_engine.models.base import Base


class KB(Base):
    __tablename__ = 'kb'
    id = Column(Integer, primary_key=True)
    round_num = Column(Integer)
    name = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
