from flask_caching import Cache
from scoring_engine.config import config


# TODO - Specifying Caching variables or no cache if set
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': config.redis_host,
    'CACHE_REDIS_PORT': config.redis_port,
})
