from flask_caching import Cache
from scoring_engine.config import config


cache = Cache(config={
    'CACHE_TYPE': config.cache_type,
    'CACHE_REDIS_HOST': config.redis_host,
    'CACHE_REDIS_PORT': config.redis_port,
    'CACHE_REDIS_PASSWORD': config.redis_password,
})

# Not cleared between rounds
agent_cache = Cache(config={
    'CACHE_TYPE': config.cache_type,
    'CACHE_REDIS_HOST': config.redis_host,
    'CACHE_REDIS_PORT': config.redis_port,
    'CACHE_REDIS_PASSWORD': config.redis_password,
    'CACHE_KEY_PREFIX': "agent_cache_",
})
