from scoring_engine.engine.job_queue import JobQueue


class WorkerQueue(JobQueue):
    def __init__(self):
        super(WorkerQueue, self).__init__()
        self.queue_name = "queued"
