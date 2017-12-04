from sqlalchemy import Column, Integer, Text, desc

from scoring_engine.models.base import Base


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text, nullable=False)

    @staticmethod
    def get_setting(name):
        return Setting.query.filter(Setting.name == name).order_by(desc(Setting.id)).first()
