from sqlalchemy import Column, Integer, Text, desc

from scoring_engine.models.base import Base
from scoring_engine.db import session


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text, nullable=False)

    @staticmethod
    def get_setting(name):
        return session.query(Setting).filter(Setting.name == name).order_by(desc(Setting.id)).first()
