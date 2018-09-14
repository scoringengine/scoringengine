from sqlalchemy import Column, Integer, Text, desc

from scoring_engine.models.base import Base
from scoring_engine.db import session


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    _value_text = Column(Text, nullable=False)
    _value_type = Column(Text, nullable=False)

    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self._value_type = self.map_value_type(kwargs['value'])
        self._value_text = self.convert_value_type(kwargs['value'])
        super(Base, self).__init__()

    def map_value_type(self, value):
        if type(value) is bool:
            return 'Boolean'
        else:
            return 'String'

    def convert_value_type(self, value):
        if self._value_type == 'Boolean':
            return bool(value)
        else:
            return str(value)

    @property
    def value(self):
        return self.convert_value_type(self._value_text)

    @value.setter
    def value(self, value):
        self._value_type = self.map_value_type(value)
        self._value_text = self.convert_value_type(value)

    @staticmethod
    def get_setting(name):
        return session.query(Setting).filter(Setting.name == name).order_by(desc(Setting.id)).first()
