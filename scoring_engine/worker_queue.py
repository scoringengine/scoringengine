import redis

from config import Config


class WorkerQueue(object):

    def __init__(self):
        config = Config()
        self.queue_name = config.redis_queue_name
        self.conn = redis.Redis(host=config.redis_host, port=config.redis_port, password=config.redis_password)

    def add_job(self, message):
        return self.conn.set(self.queue_name, message)

    def get_job(self):
        return self.conn.get(self.queue_name)
