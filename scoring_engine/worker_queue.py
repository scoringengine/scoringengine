import redis
import json

from config import Config
from job import Job


class MalformedJob(Exception):
    def __str__(self):
        return "Job must be of instance of Job class"


class WorkerQueue(object):

    def __init__(self):
        config = Config()
        self.queue_name = config.redis_queue_name
        self.conn = redis.Redis(host=config.redis_host, port=config.redis_port, password=config.redis_password)
        self.namespace = config.redis_namespace

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
