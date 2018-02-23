from flask_caching import Cache

# TODO - Specifying Caching variables or no cache if set
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'redis',
    'CACHE_REDIS_PORT': '6379',
})
