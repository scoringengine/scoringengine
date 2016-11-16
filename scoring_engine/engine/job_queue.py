import redis
import json

from scoring_engine.engine.config import Config
from scoring_engine.engine.job import Job
from scoring_engine.engine.malformed_job import MalformedJob


class JobQueue(object):
    def __init__(self):
        config = Config()
        self.queue_name = config.redis_queue_name
        self.conn = redis.Redis(host=config.redis_host, port=config.redis_port, password=config.redis_password)
        self.namespace = config.redis_namespace
        # This is meant to get overwritten by children
        self.queue_name = "jobs"

    @property
    def queue_key(self):
        return self.namespace + ':' + self.queue_name

    def size(self):
        return int(self.conn.llen(self.queue_key))

    def clear(self):
        while self.size() > 0:
            self.get_job()

    def add_job(self, job):
        if not isinstance(job, Job):
            raise MalformedJob()
        return self.conn.rpush(self.queue_key, json.dumps(job.to_dict()))

    def get_job(self):
        binary_job = self.conn.lpop(self.queue_key)
        if binary_job is None:
            return None
        encoded_job = binary_job.decode("utf-8")
        return Job.from_dict(json.loads(encoded_job))
