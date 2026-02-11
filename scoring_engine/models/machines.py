from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from scoring_engine.models.base import Base


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="unknown")
    compromised = Column(Boolean, nullable=False, default=False)
