from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from scoring_engine.models.base import Base


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    name = Column(String(100), nullable=False)
    compermised = Column(Boolean, nullable=False, default=False)
