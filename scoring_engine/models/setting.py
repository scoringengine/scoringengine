from sqlalchemy import Column, Integer, Text, desc
from time import time

from scoring_engine.models.base import Base
from scoring_engine.db import db


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    _value_text = Column(Text, nullable=False)
    _value_type = Column(Text, nullable=False)

    # In-memory cache with TTL
    _cache = {}
    _cache_ttl = 60  # Cache TTL in seconds (default: 60 seconds)

    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self._value_text = str(kwargs['value'])
        self.value = kwargs['value']
        super(Base, self).__init__()

    def map_value_type(self, value):
        if type(value) is bool:
            return 'Boolean'
        else:
            return 'String'

    def convert_value_type(self):
        if self._value_type == 'Boolean':
            if self._value_text == 'False':
                return False
            else:
                return True
        else:
            return self._value_text

    @property
    def value(self):
        return self.convert_value_type()

    @value.setter
    def value(self, value):
        self._value_type = self.map_value_type(value)
        self._value_text = str(value)

    @classmethod
    def get_setting(cls, name):
        """
        Get a setting by name with in-memory caching.
        Cache entries expire after _cache_ttl seconds.
        """
        current_time = time()

        # Check if setting is in cache and not expired
        if name in cls._cache:
            cached_value, cached_time = cls._cache[name]
            if current_time - cached_time < cls._cache_ttl:
                # Merge the cached object back into the session to avoid DetachedInstanceError
                return db.session.merge(cached_value, load=False)

        # Query database and update cache
        setting = db.session.query(Setting).filter(Setting.name == name).order_by(desc(Setting.id)).first()
        if setting:
            cls._cache[name] = (setting, current_time)
        return setting

    @classmethod
    def clear_cache(cls, name=None):
        """
        Clear the settings cache.
        If name is provided, only clear that specific setting from cache.
        Otherwise, clear the entire cache.
        """
        if name:
            cls._cache.pop(name, None)
        else:
            cls._cache.clear()
