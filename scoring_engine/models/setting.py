from sqlalchemy import Column, String, Integer, desc

from scoring_engine.models.base import Base


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)

    @staticmethod
    def get_setting(name):
        return Setting.query.filter(Setting.name == name).order_by(desc(Setting.id)).first()
