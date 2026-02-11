import json
import logging

from sqlalchemy import Column, Integer, Text, desc

from scoring_engine.db import db
from scoring_engine.models.base import Base

logger = logging.getLogger(__name__)

CACHE_PREFIX = "setting:"
CACHE_TTL = 60


def _get_redis():
    """Return a Redis client using the application config.

    Returns None when Redis is unavailable (e.g. tests running with
    cache_type=null or no Redis server).
    """
    try:
        import redis

        from scoring_engine.config import config

        if config.cache_type != "redis":
            return None
        return redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,
            decode_responses=True,
        )
    except Exception:
        return None


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    _value_text = Column(Text, nullable=False)
    _value_type = Column(Text, nullable=False)

    def __init__(self, *args, **kwargs):
        self.name = kwargs["name"]
        self._value_text = str(kwargs["value"])
        self.value = kwargs["value"]
        super(Base, self).__init__()

    def map_value_type(self, value):
        if type(value) is bool:
            return "Boolean"
        else:
            return "String"

    def convert_value_type(self):
        if self._value_type == "Boolean":
            if self._value_text == "False":
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
        """Get a setting by name with Redis caching.

        Checks Redis first (shared across all workers). On miss, queries the
        database and populates the Redis cache with a 60-second TTL.

        When Redis is unavailable the method falls back to a direct DB query.
        """
        # Try Redis cache
        r = _get_redis()
        if r is not None:
            try:
                cached = r.get(CACHE_PREFIX + name)
                if cached is not None:
                    data = json.loads(cached)
                    # Build a transient Setting without hitting the DB
                    setting = cls.__new__(cls)
                    setting.id = data["id"]
                    setting.name = name
                    setting._value_text = data["value_text"]
                    setting._value_type = data["value_type"]
                    # Merge into the current session so callers can modify + commit
                    return db.session.merge(setting, load=False)
            except Exception:
                logger.debug("Redis cache read failed for setting %s", name, exc_info=True)

        # Cache miss — query DB.
        setting = db.session.query(Setting).filter(Setting.name == name).order_by(desc(Setting.id)).first()
        if setting and r is not None:
            try:
                payload = json.dumps(
                    {
                        "id": setting.id,
                        "value_text": setting._value_text,
                        "value_type": setting._value_type,
                    }
                )
                r.set(CACHE_PREFIX + name, payload, ex=CACHE_TTL)
            except Exception:
                logger.debug("Redis cache write failed for setting %s", name, exc_info=True)
        return setting

    @classmethod
    def clear_cache(cls, name=None):
        """Clear the settings cache in Redis.

        If name is provided, only clear that specific setting.
        Otherwise, clear all cached settings.
        """
        r = _get_redis()
        if r is None:
            return
        try:
            if name:
                r.delete(CACHE_PREFIX + name)
            else:
                keys = r.keys(CACHE_PREFIX + "*")
                if keys:
                    r.delete(*keys)
        except Exception:
            logger.debug("Redis cache clear failed", exc_info=True)
